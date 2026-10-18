/**
 * 首页卡片的筛选与排序（纯函数，便于单元测试）。
 */

/**
 * 首页最多展示 limit 条预算：超支和接近上限的排前面，其次按使用比例从高到低。
 * 传入的是 /budgets/progress 的结果（只含启用的预算）。
 */
export function pickBudgets(budgets, limit = 3) {
  const rank = (b) => (b.isOverBudget ? 2 : b.isAlert ? 1 : 0)
  return [...(budgets || [])]
    .sort((a, b) => rank(b) - rank(a) || b.percentage - a.percentage)
    .slice(0, limit)
}

/**
 * 首页最多展示 limit 个进行中的目标：有截止日期的按日期从近到远，没有截止日期的排在后面（按进度从高到低）。
 */
export function pickGoals(goals, limit = 3) {
  return (goals || [])
    .filter((g) => !g.isCompleted)
    .sort((a, b) => {
      if (a.deadline && b.deadline) return a.deadline.localeCompare(b.deadline)
      if (a.deadline) return -1
      if (b.deadline) return 1
      return b.progress - a.progress
    })
    .slice(0, limit)
}

/** 距离截止还有几天；已过期返回负数，没有截止日期返回 null */
export function daysLeft(deadline, today = new Date()) {
  if (!deadline) return null
  const [y, m, d] = deadline.split('-').map(Number)
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  return Math.round((new Date(y, m - 1, d) - start) / 86400000)
}

/** 截止提示文案 */
export function deadlineText(deadline, today = new Date()) {
  const n = daysLeft(deadline, today)
  if (n === null) return ''
  if (n < 0) return `已逾期 ${-n} 天`
  if (n === 0) return '今天截止'
  return `还剩 ${n} 天`
}
