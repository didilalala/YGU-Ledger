/**
 * 报表图表的数据整理与 uCharts 配置（纯函数，不依赖 uni，便于单元测试）。
 * 统计接口只返回"有账单的日期 / 月份"，这里补全成连续的坐标轴。
 */
import uCharts from '@qiun/ucharts'

export const COLORS = {
  expense: '#e5484d',
  income: '#16a34a',
  // 饼图调色板，对比度够的 8 种颜色循环使用
  palette: ['#4f6ef7', '#f59e0b', '#16a34a', '#e5484d', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'],
}

const MAX_SLICES = 8

/**
 * 分类占比 → 饼图系列。超过 MAX_SLICES 个分类时，把末尾的合并成"其他"，否则小块挤在一起看不清。
 * @param {{categoryName: string, amount: number}[]} items 已按金额从大到小排序
 */
export function buildPieSeries(items) {
  const list = (items || []).filter((i) => i.amount > 0)
  const head = list.slice(0, MAX_SLICES)
  const rest = list.slice(MAX_SLICES)
  const data = head.map((i) => ({ name: i.categoryName, value: i.amount }))
  if (rest.length) data.push({ name: '其他', value: rest.reduce((sum, i) => sum + i.amount, 0) })
  return [{ data }]
}

const pad = (n) => String(n).padStart(2, '0')

/** 月视图：补全当月每一天。trend 的 period 形如 '2026-10-05' */
export function fillDailyTrend(trend, year, month) {
  const days = new Date(year, month, 0).getDate()
  const byPeriod = new Map((trend || []).map((t) => [t.period, t]))
  const categories = []
  const income = []
  const expense = []
  for (let d = 1; d <= days; d++) {
    const t = byPeriod.get(`${year}-${pad(month)}-${pad(d)}`)
    categories.push(String(d))
    income.push(t ? t.income : 0)
    expense.push(t ? t.expense : 0)
  }
  return { categories, income, expense }
}

/** 年视图：补全 12 个月。trend 的 period 形如 '2026-10' */
export function fillMonthlyTrend(trend, year) {
  const byPeriod = new Map((trend || []).map((t) => [t.period, t]))
  const categories = []
  const income = []
  const expense = []
  for (let m = 1; m <= 12; m++) {
    const t = byPeriod.get(`${year}-${pad(m)}`)
    categories.push(`${m}月`)
    income.push(t ? t.income : 0)
    expense.push(t ? t.expense : 0)
  }
  return { categories, income, expense }
}

/** 补全后的趋势 → 折线 / 柱状图系列 */
export function buildTrendSeries({ income, expense }) {
  return [
    { name: '支出', data: expense, color: COLORS.expense },
    { name: '收入', data: income, color: COLORS.income },
  ]
}

export const hasData = (filled) => [...filled.income, ...filled.expense].some((v) => v > 0)

/**
 * 生成 uCharts 的构造参数。
 * width / height 是绘图缓冲区的像素大小（= 显示尺寸 × pixelRatio），与组件里的 canvas 缩放配合使用。
 */
export function buildChartOptions({ type, categories, series, width, height, pixelRatio = 1, animation = true }) {
  const base = {
    type,
    width,
    height,
    pixelRatio,
    animation,
    duration: 600,
    background: '#FFFFFF',
    categories,
    series,
    padding: [15, 15, 5, 5].map((v) => v * pixelRatio),
    legend: { show: type !== 'pie' && type !== 'ring', position: 'top', float: 'right' },
    fontSize: 11 * pixelRatio,
    enableScroll: false,
  }
  if (type === 'ring' || type === 'pie') {
    return {
      ...base,
      padding: [5, 5, 5, 5].map((v) => v * pixelRatio),
      legend: { show: true, position: 'bottom', float: 'center', itemGap: 12 * pixelRatio },
      dataLabel: true,
      extra: { ring: { ringWidth: 28 * pixelRatio, linearType: 'none', border: true, borderWidth: 2 * pixelRatio, borderColor: '#FFFFFF', labelWidth: 12 * pixelRatio }, pie: { border: true, borderWidth: 2 * pixelRatio, borderColor: '#FFFFFF', labelWidth: 12 * pixelRatio } },
      color: COLORS.palette,
    }
  }
  return {
    ...base,
    dataLabel: false,
    dataPointShape: type === 'line',
    xAxis: { disableGrid: true, labelCount: 7, fontSize: 11 * pixelRatio, boundaryGap: type === 'column' ? 'justify' : 'center' },
    yAxis: { gridType: 'dash', dashLength: 4 * pixelRatio, gridColor: '#e8e9ee', splitNumber: 4, data: [{ min: 0, fontSize: 11 * pixelRatio }] },
    extra: {
      line: { type: 'curve', width: 2 * pixelRatio, activeType: 'hollow' },
      column: { type: 'group', width: 10 * pixelRatio, seriesGap: 2 * pixelRatio, barBorderRadius: [3 * pixelRatio, 3 * pixelRatio, 0, 0] },
    },
  }
}

/** 创建图表实例。context 为 uni.createCanvasContext 的返回值 */
export function createChart(context, options) {
  return new uCharts({ ...options, context })
}
