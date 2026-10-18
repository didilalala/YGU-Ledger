/**
 * 账单列表的筛选与分组（纯函数，不依赖 uni，便于单元测试）。
 */
import { monthRange, toDateString } from './format.js'

export const DATE_PRESETS = [
  { key: 'all', label: '全部' },
  { key: 'thisMonth', label: '本月' },
  { key: 'lastMonth', label: '上月' },
  { key: 'last30', label: '近30天' },
]

/** 预设 → { startDate, endDate }；'all' 返回空对象（不限日期） */
export function presetRange(key, today = new Date()) {
  if (key === 'thisMonth') return monthRange(today)
  if (key === 'lastMonth') return monthRange(new Date(today.getFullYear(), today.getMonth() - 1, 1))
  if (key === 'last30') {
    const start = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 29)
    return { startDate: toDateString(start), endDate: toDateString(today) }
  }
  return {}
}

/** 当前日期区间恰好等于某个预设时返回它的 key，否则返回 null（自定义区间） */
export function matchPreset(startDate, endDate, today = new Date()) {
  for (const { key } of DATE_PRESETS) {
    const r = presetRange(key, today)
    if ((r.startDate || '') === (startDate || '') && (r.endDate || '') === (endDate || '')) return key
  }
  return null
}

/** 按月分组，保持原有顺序（列表按日期排序，同月的账单是连续的）。返回 [{ month: '2026-10', items }] */
export function groupByMonth(items) {
  const groups = []
  for (const item of items) {
    const month = item.date.slice(0, 7)
    const last = groups[groups.length - 1]
    if (last && last.month === month) last.items.push(item)
    else groups.push({ month, items: [item] })
  }
  return groups
}

/** 用统计接口的月度趋势（[{period, income, expense}]）建立 月份 → 小计 的映射 */
export function monthlyTotals(trend) {
  return Object.fromEntries((trend || []).map((t) => [t.period, { income: t.income, expense: t.expense }]))
}

/** '2026-10' → '2026年10月' */
export const monthLabel = (month) => `${month.slice(0, 4)}年${Number(month.slice(5, 7))}月`
