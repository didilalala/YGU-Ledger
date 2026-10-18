/**
 * 统计页的数据整理（纯函数，不依赖 uni，便于单元测试）。
 * 统计接口只返回"有账单的日期 / 月份"，这里补全成界面需要的完整网格。
 */
import { COLORS } from './chart.js'
import { monthRange, toDateString } from './format.js'

export const WEEK_DAYS = ['一', '二', '三', '四', '五', '六', '日']
const pad = (n) => String(n).padStart(2, '0')

/** 统计接口的趋势数组 → { period: { income, expense } } */
export function trendToMap(trend) {
  return Object.fromEntries((trend || []).map((t) => [t.period, { income: t.income || 0, expense: t.expense || 0 }]))
}

/** 日历格里的金额：0 不显示，≥1 万缩写为 x.xw，其余保留两位小数 */
export function formatCellAmount(value) {
  if (!value) return ''
  if (value >= 10000) return `${(value / 10000).toFixed(1)}w`
  return value.toFixed(2)
}

/**
 * 月日历：周一为每周第一天，前面用空格子补齐。未来的日期标记为 isFuture（灰显，不可点）。
 * @param {number} month0 0 起始的月份
 * @param {string} todayStr YYYY-MM-DD
 */
export function buildCalendarCells(year, month0, dailyMap, todayStr) {
  const days = new Date(year, month0 + 1, 0).getDate()
  const firstWeekday = new Date(year, month0, 1).getDay() // 0 = 周日
  const offset = firstWeekday === 0 ? 6 : firstWeekday - 1
  const cells = []
  for (let i = 0; i < offset; i++) cells.push({ key: `empty-${i}`, empty: true })
  for (let d = 1; d <= days; d++) {
    const dateStr = `${year}-${pad(month0 + 1)}-${pad(d)}`
    const data = dailyMap[dateStr] || { income: 0, expense: 0 }
    const isFuture = dateStr > todayStr
    cells.push({
      key: dateStr, empty: false, day: d, dateStr, isFuture, isToday: dateStr === todayStr,
      income: isFuture ? 0 : data.income, expense: isFuture ? 0 : data.expense,
    })
  }
  return cells
}

/** 12 个月的格子（年内按月汇总）；未来的月份标记为 isFuture */
export function buildMonthCells(year, monthlyMap, today = new Date()) {
  return Array.from({ length: 12 }, (_, i) => {
    const key = `${year}-${pad(i + 1)}`
    const data = monthlyMap[key] || { income: 0, expense: 0 }
    const isFuture = year > today.getFullYear() || (year === today.getFullYear() && i > today.getMonth())
    return {
      key, month: i + 1, label: `${i + 1}月`, isFuture,
      isCurrent: year === today.getFullYear() && i === today.getMonth(),
      income: isFuture ? 0 : data.income, expense: isFuture ? 0 : data.expense,
    }
  })
}

/** 最近 count 年（含今年）的汇总，旧的在前。monthlyMap 的 key 为 YYYY-MM */
export function buildYearCells(monthlyMap, count = 5, today = new Date()) {
  const totals = {}
  for (const [key, v] of Object.entries(monthlyMap)) {
    const y = Number(key.slice(0, 4))
    totals[y] = totals[y] || { income: 0, expense: 0 }
    totals[y].income += v.income
    totals[y].expense += v.expense
  }
  const current = today.getFullYear()
  return Array.from({ length: count }, (_, i) => {
    const year = current - (count - 1 - i)
    const t = totals[year] || { income: 0, expense: 0 }
    return { year, label: String(year), isCurrent: year === current, income: t.income, expense: t.expense }
  })
}

/** 最近 count 个月（含本月），旧的在前 */
export function lastMonths(count = 12, today = new Date()) {
  return Array.from({ length: count }, (_, i) => {
    const d = new Date(today.getFullYear(), today.getMonth() - (count - 1 - i), 1)
    return { year: d.getFullYear(), month: d.getMonth() + 1, key: `${d.getFullYear()}-${pad(d.getMonth() + 1)}`, label: `${d.getMonth() + 1}月` }
  })
}

/** 一组月份对应的起止日期（最后一个月取整月，不截到今天；统计接口按日期过滤，未来没有账单） */
export function rangeOfMonths(months) {
  const first = months[0]
  const last = months[months.length - 1]
  return {
    startDate: monthRange(new Date(first.year, first.month - 1, 1)).startDate,
    endDate: monthRange(new Date(last.year, last.month - 1, 1)).endDate,
  }
}

/** 资产变动趋势：把每月净额（收入 - 支出）逐月累加 */
export function cumulativeNet(months, monthlyMap) {
  let running = 0
  const values = months.map((m) => {
    const d = monthlyMap[m.key] || { income: 0, expense: 0 }
    running += d.income - d.expense
    return Math.round(running * 100) / 100
  })
  return { categories: months.map((m) => m.label), values }
}

/** 分类构成的图例行：取前 limit 个，其余合并为"其他"，颜色与饼图调色板一一对应 */
export function compositionRows(items, limit = 8) {
  const list = (items || []).filter((i) => i.amount > 0)
  const total = list.reduce((sum, i) => sum + i.amount, 0)
  const head = list.slice(0, limit).map((i) => ({ name: i.categoryName, icon: i.categoryIcon, amount: i.amount }))
  const rest = list.slice(limit)
  if (rest.length) head.push({ name: '其他', icon: '📦', amount: rest.reduce((s, i) => s + i.amount, 0) })
  return head.map((r, idx) => ({
    ...r,
    color: COLORS.palette[idx % COLORS.palette.length],
    percent: total ? Math.round((r.amount / total) * 100) : 0,
  }))
}

/** 有收支记录的天，按日期升序，用于"每日收支"列表 */
export function dailySummary(trend) {
  return (trend || [])
    .filter((t) => (t.income || 0) > 0 || (t.expense || 0) > 0)
    .map((t) => ({ date: t.period, day: Number(t.period.slice(8, 10)), income: t.income || 0, expense: t.expense || 0 }))
    .sort((a, b) => a.date.localeCompare(b.date))
}

export const todayString = (today = new Date()) => toDateString(today)
