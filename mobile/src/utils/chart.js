/**
 * 报表图表的数据整理与 uCharts 配置（纯函数，不依赖 uni，便于单元测试）。
 * 统计接口只返回"有账单的日期 / 月份"，这里补全成连续的坐标轴。
 */
import uCharts from '@qiun/ucharts'

export const COLORS = {
  expense: '#ff7a6e',
  income: '#5cc9a0',
  // 饼图调色板，对比度够的 8 种颜色循环使用
  palette: ['#8f78e6', '#ffd86b', '#5cc9a0', '#ff7a6e', '#8fc0fa', '#ff9ec4', '#ffae7a', '#7fd8e8'],
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
 * ⚠️ uCharts 内部会把字号、线宽、间距、内边距统一乘以 pixelRatio，所以这里的长度都写"显示像素"，不要再预先乘一次。
 *
 * @param {{title?: string, subtitle?: string}} [center] 圆环中心的文字（如总计金额）
 */
export function buildChartOptions({ type, categories, series, width, height, pixelRatio = 1, animation = true, center = null }) {
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
    padding: [15, 15, 5, 5],
    legend: { show: type !== 'pie' && type !== 'ring' && series.length > 1, position: 'top', float: 'right' },
    fontSize: 11,
    enableScroll: false,
  }
  if (type === 'ring' || type === 'pie') {
    return {
      ...base,
      ...(center && type === 'ring'
        ? {
            title: { name: center.title, fontSize: 14, color: '#2F2A5C', offsetY: -4 },
            subtitle: { name: center.subtitle || '', fontSize: 10, color: '#6F6A9C', offsetY: 8 },
          }
        : {}),
      padding: [5, 5, 5, 5],
      legend: { show: !center, position: 'bottom', float: 'center', itemGap: 12 },
      dataLabel: !center,
      extra: {
        ring: { ringWidth: 20, linearType: 'none', border: true, borderWidth: 2, borderColor: '#FFFFFF', labelWidth: 12 },
        pie: { border: true, borderWidth: 2, borderColor: '#FFFFFF', labelWidth: 12 },
      },
      color: COLORS.palette,
    }
  }
  return {
    ...base,
    dataLabel: false,
    dataPointShape: type === 'line' || type === 'area',
    xAxis: { disableGrid: true, labelCount: 6, fontSize: 11, boundaryGap: type === 'column' ? 'justify' : 'center' },
    yAxis: { gridType: 'dash', dashLength: 4, gridColor: '#e8e2f8', splitNumber: 4, data: [{ min: 0, fontSize: 11 }] },
    extra: {
      line: { type: 'curve', width: 2, activeType: 'hollow' },
      area: { type: 'curve', opacity: 0.3, addLine: true, width: 3, gradient: true },
      column: { type: 'group', width: 10, seriesGap: 2, barBorderRadius: [3, 3, 0, 0] },
    },
  }
}

/** 创建图表实例。context 为 uni.createCanvasContext 的返回值 */
export function createChart(context, options) {
  return new uCharts({ ...options, context })
}
