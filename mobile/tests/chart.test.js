import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildChartOptions, buildPieSeries, buildTrendSeries, createChart, fillDailyTrend, fillMonthlyTrend, hasData,
} from '../src/utils/chart.js'

test('buildPieSeries 过滤 0 金额，超过 8 个分类时合并为"其他"', () => {
  const items = Array.from({ length: 10 }, (_, i) => ({ categoryName: `分类${i}`, amount: 100 - i * 10 }))
  items.push({ categoryName: '空', amount: 0 })
  const { data } = buildPieSeries(items)[0]
  assert.equal(data.length, 9)
  assert.deepEqual(data[8], { name: '其他', value: 20 + 10 }) // 分类8(20) + 分类9(10)
  assert.deepEqual(buildPieSeries([{ categoryName: 'a', amount: 5 }])[0].data, [{ name: 'a', value: 5 }])
  assert.deepEqual(buildPieSeries(undefined)[0].data, [])
})

test('fillDailyTrend 补全整月，缺失的日子为 0', () => {
  const r = fillDailyTrend([{ period: '2026-10-05', income: 100, expense: 30 }], 2026, 10)
  assert.equal(r.categories.length, 31)
  assert.equal(r.categories[4], '5')
  assert.equal(r.income[4], 100)
  assert.equal(r.expense[4], 30)
  assert.equal(r.expense[0], 0)
  assert.equal(fillDailyTrend([], 2024, 2).categories.length, 29) // 闰年
  assert.equal(fillDailyTrend([], 2026, 2).categories.length, 28)
})

test('fillMonthlyTrend 补全 12 个月', () => {
  const r = fillMonthlyTrend([{ period: '2026-03', income: 0, expense: 80 }], 2026)
  assert.equal(r.categories.length, 12)
  assert.equal(r.categories[2], '3月')
  assert.equal(r.expense[2], 80)
  assert.equal(r.expense[3], 0)
})

test('buildTrendSeries / hasData', () => {
  const filled = fillDailyTrend([{ period: '2026-10-05', income: 0, expense: 30 }], 2026, 10)
  const series = buildTrendSeries(filled)
  assert.deepEqual(series.map((s) => s.name), ['支出', '收入'])
  assert.equal(hasData(filled), true)
  assert.equal(hasData(fillDailyTrend([], 2026, 10)), false)
})

/** 记录绘制调用的假 canvas 上下文（uCharts 使用 uni 旧版 canvas 接口） */
function fakeContext() {
  const calls = []
  const texts = []
  const ctx = new Proxy({}, {
    get(_, name) {
      if (name === 'measureText') return (t) => ({ width: String(t).length * 7 })
      if (name === 'createLinearGradient' || name === 'createCircularGradient') return () => ({ addColorStop() {} })
      if (name === 'fillText') return (t) => { texts.push(String(t)); calls.push(name) }
      return () => { calls.push(name) }
    },
    set: () => true,
  })
  return { ctx, calls, texts }
}

/** uCharts 的绘制是异步的（内部用定时器），等到出现 draw 调用再返回 */
const draw = async (type, categories, series) => {
  const { ctx, calls, texts } = fakeContext()
  createChart(ctx, buildChartOptions({ type, categories, series, width: 600, height: 400, pixelRatio: 2, animation: false }))
  for (let i = 0; i < 100 && !calls.includes('draw'); i++) await new Promise((r) => setTimeout(r, 20))
  return { calls, texts }
}

test('uCharts 能用我们的配置画出环形图', async () => {
  const { calls, texts } = await draw('ring', [], buildPieSeries([{ categoryName: '餐饮', amount: 70 }, { categoryName: '交通', amount: 30 }]))
  assert.ok(calls.includes('arc') && calls.includes('draw'), '应当有 arc 和 draw 调用')
  assert.ok(texts.some((t) => t.includes('餐饮')), `图例应包含分类名，实际：${texts}`)
  assert.ok(texts.includes('70%'), '扇区上显示占比')
})

test('uCharts 能画出月视图折线图', async () => {
  const filled = fillDailyTrend([{ period: '2026-10-05', income: 100, expense: 30 }], 2026, 10)
  const { calls, texts } = await draw('line', filled.categories, buildTrendSeries(filled))
  assert.ok(calls.includes('lineTo') && calls.includes('draw'))
  assert.ok(texts.includes('支出') && texts.includes('收入'), '图例')
  assert.ok(texts.includes('1'), 'x 轴标签')
})

test('uCharts 能画出年视图柱状图', async () => {
  const filled = fillMonthlyTrend([{ period: '2026-03', income: 500, expense: 80 }], 2026)
  const { calls, texts } = await draw('column', filled.categories, buildTrendSeries(filled))
  assert.ok(calls.includes('fillRect') || calls.includes('fill'))
  assert.ok(texts.some((t) => t.endsWith('月')))
})

test('全 0 数据也能正常画出', async () => {
  const filled = fillDailyTrend([], 2026, 10)
  const { calls } = await draw('line', filled.categories, buildTrendSeries(filled))
  assert.ok(calls.includes('draw'))
})
