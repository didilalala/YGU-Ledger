/**
 * AI 聊天页的展示逻辑（纯函数，便于单元测试）。
 * 后端通过 SSE 推送的工具结果字段已经转成驼峰（total_expense → totalExpense）。
 */

/** 账单预览卡的配色：支出偏橙、收入偏绿，与原项目一致 */
export const BILL_TONES = {
  expense: { bg: '#FFF1EE', border: '#FFC7BF', iconBg: '#FFC7BF', amount: '#E0564D' },
  income: { bg: '#E6F8F0', border: '#BFEBD8', iconBg: '#BFEBD8', amount: '#2A9D76' },
}

const money = (v) => `¥${Number(v || 0).toFixed(2)}`

/**
 * 工具结果 → 聊天里怎么展示。
 * @returns {{kind: 'bills'|'stats'|'list'|'text'|'error', title: string, [key: string]: any}}
 */
export function describeToolResult(toolName, result) {
  if (!result?.success) return { kind: 'error', title: result?.message || '操作失败' }
  const data = result.data || {}
  if (toolName === 'create_bills') {
    return { kind: 'bills', title: result.message, bills: (data.bills || []).map((b) => ({ ...b, saved: false })) }
  }
  if (toolName === 'get_statistics') {
    return {
      kind: 'stats',
      title: result.message,
      rows: [
        { label: '总支出', value: money(data.totalExpense), tone: 'expense' },
        { label: '总收入', value: money(data.totalIncome), tone: 'income' },
        { label: '结余', value: money(data.balance), tone: 'plain' },
      ],
    }
  }
  if (toolName === 'query_bills') {
    return {
      kind: 'list',
      title: result.message,
      items: (data.items || []).map((b) => ({
        id: b.id, date: b.date, description: b.description || b.categoryName || '未分类',
        type: b.type, amount: `${b.type === 'income' ? '+' : '-'}${money(b.amount)}`,
      })),
    }
  }
  return { kind: 'text', title: result.message }
}

/** 一条识别出的账单能否保存：必须匹配到分类（后端要校验分类归属），且还没保存过 */
export const canSaveBill = (bill) => !!bill.categoryId && !bill.saved

/** 所有消息里待保存的账单 */
export function pendingBills(messages) {
  return messages.flatMap((m) => (m.bills || []).filter(canSaveBill))
}

/** 账单卡右侧金额，如 "-¥26.80" */
export const billAmountText = (bill) => `${bill.type === 'income' ? '+' : '-'}¥${Number(bill.amount).toFixed(2)}`

/** 思考耗时文案：毫秒 → "用时 35 秒" / "用时 1.2 秒" */
export function thinkingText(ms) {
  if (!ms && ms !== 0) return '已深度思考'
  const sec = ms / 1000
  return `已深度思考（用时 ${sec >= 10 ? Math.round(sec) : sec.toFixed(1)} 秒）`
}
