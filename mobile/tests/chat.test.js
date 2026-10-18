import test from 'node:test'
import assert from 'node:assert/strict'
import { billAmountText, canSaveBill, describeToolResult, pendingBills, thinkingText } from '../src/utils/chat.js'

test('统计结果 → 三行：总支出 / 总收入 / 结余', () => {
  const r = describeToolResult('get_statistics', { success: true, message: '统计数据获取成功', data: { totalExpense: 301.34, totalIncome: 600, balance: 298.66 } })
  assert.equal(r.kind, 'stats')
  assert.deepEqual(r.rows.map((x) => [x.label, x.value, x.tone]), [['总支出', '¥301.34', 'expense'], ['总收入', '¥600.00', 'income'], ['结余', '¥298.66', 'plain']])
})

test('查询结果 → 列表，金额带正负号，缺描述时用分类名', () => {
  const r = describeToolResult('query_bills', { success: true, message: '查询到 2 条账单', data: { items: [
    { id: 1, date: '2026-10-18', description: '外卖', type: 'expense', amount: 26.8, categoryName: '餐饮' },
    { id: 2, date: '2026-10-17', description: '', type: 'income', amount: 100, categoryName: '兼职' },
  ] } })
  assert.equal(r.kind, 'list')
  assert.deepEqual(r.items.map((i) => [i.description, i.amount]), [['外卖', '-¥26.80'], ['兼职', '+¥100.00']])
})

test('记账结果 → 账单卡，初始都是未保存', () => {
  const r = describeToolResult('create_bills', { success: true, message: '识别到 1 条账单', data: { bills: [{ amount: 8, type: 'expense', categoryId: 3 }] } })
  assert.equal(r.kind, 'bills')
  assert.equal(r.bills[0].saved, false)
})

test('失败与其他工具', () => {
  assert.deepEqual(describeToolResult('get_statistics', { success: false, message: '日期有误' }), { kind: 'error', title: '日期有误' })
  assert.equal(describeToolResult('x', undefined).title, '操作失败')
  assert.deepEqual(describeToolResult('delete_bills', { success: true, message: '成功删除 2 条账单', data: {} }), { kind: 'text', title: '成功删除 2 条账单' })
})

test('待保存：必须有分类且未保存', () => {
  assert.equal(canSaveBill({ categoryId: 1, saved: false }), true)
  assert.equal(canSaveBill({ categoryId: null, saved: false }), false)
  assert.equal(canSaveBill({ categoryId: 1, saved: true }), false)
  const messages = [{ bills: [{ categoryId: 1 }, { categoryId: null }, { categoryId: 2, saved: true }] }, { bills: [] }, {}, { bills: [{ categoryId: 5 }] }]
  assert.equal(pendingBills(messages).length, 2)
})

test('金额与思考耗时文案', () => {
  assert.equal(billAmountText({ type: 'expense', amount: 26.8 }), '-¥26.80')
  assert.equal(billAmountText({ type: 'income', amount: 5 }), '+¥5.00')
  assert.equal(thinkingText(35000), '已深度思考（用时 35 秒）')
  assert.equal(thinkingText(1234), '已深度思考（用时 1.2 秒）')
  assert.equal(thinkingText(undefined), '已深度思考')
})
