import test from 'node:test'
import assert from 'node:assert/strict'
import { groupByMonth, matchPreset, monthLabel, monthlyTotals, presetRange } from '../src/utils/bill-filter.js'

const today = new Date(2026, 9, 18) // 2026-10-18

test('presetRange 本月 / 上月 / 近30天 / 全部', () => {
  assert.deepEqual(presetRange('thisMonth', today), { startDate: '2026-10-01', endDate: '2026-10-31' })
  assert.deepEqual(presetRange('lastMonth', today), { startDate: '2026-09-01', endDate: '2026-09-30' })
  assert.deepEqual(presetRange('last30', today), { startDate: '2026-09-19', endDate: '2026-10-18' })
  assert.deepEqual(presetRange('all', today), {})
})

test('presetRange 上月跨年、闰年二月', () => {
  assert.deepEqual(presetRange('lastMonth', new Date(2026, 0, 5)), { startDate: '2025-12-01', endDate: '2025-12-31' })
  assert.deepEqual(presetRange('lastMonth', new Date(2024, 2, 5)), { startDate: '2024-02-01', endDate: '2024-02-29' })
})

test('matchPreset 识别预设，自定义区间返回 null', () => {
  assert.equal(matchPreset('2026-10-01', '2026-10-31', today), 'thisMonth')
  assert.equal(matchPreset('', '', today), 'all')
  assert.equal(matchPreset(undefined, undefined, today), 'all')
  assert.equal(matchPreset('2026-10-05', '2026-10-31', today), null)
})

test('groupByMonth 按月连续分组', () => {
  const items = [{ id: 1, date: '2026-10-20' }, { id: 2, date: '2026-10-01' }, { id: 3, date: '2026-09-30' }]
  const groups = groupByMonth(items)
  assert.deepEqual(groups.map((g) => [g.month, g.items.map((i) => i.id)]), [['2026-10', [1, 2]], ['2026-09', [3]]])
  assert.deepEqual(groupByMonth([]), [])
})

test('monthlyTotals / monthLabel', () => {
  assert.deepEqual(monthlyTotals([{ period: '2026-10', income: 100, expense: 40 }]), { '2026-10': { income: 100, expense: 40 } })
  assert.deepEqual(monthlyTotals(undefined), {})
  assert.equal(monthLabel('2026-09'), '2026年9月')
})
