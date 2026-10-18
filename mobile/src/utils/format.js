/**
 * 格式化工具。对应原项目 utils/format.ts、utils/date.ts。
 */

/** 金额：保留两位小数，带千分位 */
export function formatMoney(value) {
  const num = Number(value) || 0
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** 带正负号的金额，收入为 +，支出为 - */
export function formatSignedMoney(amount, type) {
  return `${type === 'income' ? '+' : '-'}${formatMoney(amount)}`
}

function pad(n) {
  return String(n).padStart(2, '0')
}

/** Date → YYYY-MM-DD（本地时区） */
export function toDateString(date = new Date()) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** 当月第一天和最后一天 */
export function monthRange(date = new Date()) {
  const start = new Date(date.getFullYear(), date.getMonth(), 1)
  const end = new Date(date.getFullYear(), date.getMonth() + 1, 0)
  return { startDate: toDateString(start), endDate: toDateString(end) }
}

/**
 * 解析用户输入的金额，允许负数（如信用卡欠款）和千分位逗号。
 * 不是合法数字时返回 NaN，调用方据此提示。
 */
export function parseAmount(input) {
  const text = String(input ?? '').trim().replace(/,/g, '')
  if (!/^-?\d+(\.\d+)?$/.test(text)) return NaN
  return Number(text)
}
