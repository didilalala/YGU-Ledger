import test from 'node:test'
import assert from 'node:assert/strict'
import { daysLeft, deadlineText, pickBudgets, pickGoals } from '../src/utils/dashboard.js'
import { parseAmount } from '../src/utils/format.js'

const b = (id, percentage, extra = {}) => ({ id, percentage, isAlert: false, isOverBudget: false, ...extra })

test('pickBudgets 超支 > 预警 > 使用比例，最多取 limit 条', () => {
  const list = [b(1, 90), b(2, 40), b(3, 85, { isAlert: true }), b(4, 120, { isAlert: true, isOverBudget: true })]
  assert.deepEqual(pickBudgets(list, 3).map((x) => x.id), [4, 3, 1])
  assert.deepEqual(pickBudgets(list, 10).map((x) => x.id), [4, 3, 1, 2])
})

test('pickBudgets 不修改原数组，空值安全', () => {
  const list = [b(1, 10), b(2, 90)]
  pickBudgets(list)
  assert.deepEqual(list.map((x) => x.id), [1, 2])
  assert.deepEqual(pickBudgets(undefined), [])
})

const g = (id, progress, deadline, isCompleted = false) => ({ id, progress, deadline, isCompleted })

test('pickGoals 跳过已完成，有截止日期的在前并按日期排序', () => {
  const list = [g(1, 80, null), g(2, 10, '2027-03-01'), g(3, 50, '2026-12-01'), g(4, 100, '2026-11-01', true), g(5, 20, null)]
  assert.deepEqual(pickGoals(list, 10).map((x) => x.id), [3, 2, 1, 5])
  assert.deepEqual(pickGoals(list, 2).map((x) => x.id), [3, 2])
  assert.deepEqual(pickGoals(undefined), [])
})

const today = new Date(2026, 9, 18)

test('daysLeft / deadlineText', () => {
  assert.equal(daysLeft('2026-10-18', today), 0)
  assert.equal(daysLeft('2026-10-28', today), 10)
  assert.equal(daysLeft('2026-10-15', today), -3)
  assert.equal(daysLeft('2027-01-01', today), 75)
  assert.equal(daysLeft(null, today), null)
  assert.equal(deadlineText('2026-10-28', today), '还剩 10 天')
  assert.equal(deadlineText('2026-10-18', today), '今天截止')
  assert.equal(deadlineText('2026-10-15', today), '已逾期 3 天')
  assert.equal(deadlineText(null, today), '')
})

test('daysLeft 跨夏令时 / 跨年也按整天计算', () => {
  assert.equal(daysLeft('2027-01-01', new Date(2026, 11, 31, 23, 59)), 1)
})


test('parseAmount 支持负数、千分位、小数，非法输入返回 NaN', () => {
  assert.equal(parseAmount('100'), 100)
  assert.equal(parseAmount(' 12.5 '), 12.5)
  assert.equal(parseAmount('-300'), -300)
  assert.equal(parseAmount('1,234.50'), 1234.5)
  assert.equal(parseAmount('0'), 0)
  for (const bad of ['', '  ', 'abc', '1.', '.5', '--1', '1-', '1e3', null, undefined]) {
    assert.ok(Number.isNaN(parseAmount(bad)), `应为 NaN：${JSON.stringify(bad)}`)
  }
})
