/**
 * 解析出的账单草稿 → 确认弹窗文案 / 提交给后端的数据（纯函数）。
 */

/** 弹窗内容，如 "支出 ¥23.50\n微信支付\n2026-10-18" */
export function describeBill(bill) {
  const kind = bill.type === 'income' ? '收入' : '支出'
  return `${kind} ¥${bill.amount.toFixed(2)}\n${bill.description}\n${bill.date}`
}

/** 提交给 POST /bills 的数据。通知原文放在备注里，方便事后核对；分类留空，由用户之后补充 */
export function toBillPayload(bill) {
  return {
    amount: bill.amount,
    type: bill.type,
    description: bill.description,
    date: bill.date,
    source: 'notification',
    notes: bill.raw,
  }
}
