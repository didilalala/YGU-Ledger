import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildCalendarCells, buildMonthCells, buildYearCells, compositionRows, cumulativeNet, dailySummary,
  formatCellAmount, lastMonths, rangeOfMonths, trendToMap,
} from '../src/utils/report.js'

test('trendToMap / formatCellAmount', () => {
  assert.deepEqual(trendToMap([{ period: '2026-10-05', income: 100, expense: 30 }]), { '2026-10-05': { income: 100, expense: 30 } })
  assert.deepEqual(trendToMap(undefined), {})
  assert.equal(formatCellAmount(0), '')
  assert.equal(formatCellAmount(12.5), '12.50')
  assert.equal(formatCellAmount(10000), '1.0w')
  assert.equal(formatCellAmount(23456), '2.3w')
})

test('日历：2026 年 10 月 1 日是周四 → 周一为首列，前面补 3 个空格', () => {
  const cells = buildCalendarCells(2026, 9, {}, '2026-10-18')
  assert.equal(cells.filter((c) => c.empty).length, 3)
  assert.equal(cells.filter((c) => !c.empty).length, 31)
  assert.equal(cells[3].dateStr, '2026-10-01')
})

test('日历：周日开头的月份补 6 个空格（2026 年 2 月 1 日是周日）', () => {
  const cells = buildCalendarCells(2026, 1, {}, '2026-10-18')
  assert.equal(cells.filter((c) => c.empty).length, 6)
  assert.equal(cells.filter((c) => !c.empty).length, 28)
})

test('日历：未来日期清零并标记，今天高亮，有数据的日期带金额', () => {
  const map = { '2026-10-18': { income: 0, expense: 26.8 }, '2026-10-25': { income: 5, expense: 5 } }
  const cells = buildCalendarCells(2026, 9, map, '2026-10-18').filter((c) => !c.empty)
  const today = cells.find((c) => c.dateStr === '2026-10-18')
  assert.deepEqual([today.isToday, today.expense, today.isFuture], [true, 26.8, false])
  const future = cells.find((c) => c.dateStr === '2026-10-25')
  assert.deepEqual([future.isFuture, future.income, future.expense], [true, 0, 0])
})

test('月格：12 个月，未来月份标记，当月标记', () => {
  const cells = buildMonthCells(2026, { '2026-03': { income: 100, expense: 40 } }, new Date(2026, 9, 18))
  assert.equal(cells.length, 12)
  assert.deepEqual([cells[2].income, cells[2].expense], [100, 40])
  assert.equal(cells[9].isCurrent, true)
  assert.equal(cells[10].isFuture, true)
  assert.equal(buildMonthCells(2027, {}, new Date(2026, 9, 18)).every((c) => c.isFuture), true)
})

test('年格：最近 5 年，按年汇总月数据', () => {
  const cells = buildYearCells({ '2026-01': { income: 10, expense: 1 }, '2026-02': { income: 20, expense: 2 }, '2024-05': { income: 7, expense: 3 } }, 5, new Date(2026, 9, 18))
  assert.deepEqual(cells.map((c) => c.year), [2022, 2023, 2024, 2025, 2026])
  assert.deepEqual([cells[4].income, cells[4].expense, cells[4].isCurrent], [30, 3, true])
  assert.equal(cells[2].income, 7)
  assert.equal(cells[0].income, 0)
})

test('lastMonths 跨年，rangeOfMonths 取首月 1 号到末月月底', () => {
  const months = lastMonths(12, new Date(2026, 2, 7))
  assert.equal(months[0].key, '2025-04')
  assert.equal(months[11].key, '2026-03')
  assert.deepEqual(rangeOfMonths(months), { startDate: '2025-04-01', endDate: '2026-03-31' })
})

test('cumulativeNet 逐月累加净额', () => {
  const months = lastMonths(3, new Date(2026, 9, 18))
  const r = cumulativeNet(months, { '2026-08': { income: 100, expense: 30 }, '2026-10': { income: 0, expense: 50.5 } })
  assert.deepEqual(r.categories, ['8月', '9月', '10月'])
  assert.deepEqual(r.values, [70, 70, 19.5])
})

test('compositionRows 占比、颜色、合并其他', () => {
  const items = Array.from({ length: 10 }, (_, i) => ({ categoryName: `c${i}`, categoryIcon: '🍔', amount: 10 }))
  const rows = compositionRows(items, 8)
  assert.equal(rows.length, 9)
  assert.deepEqual([rows[8].name, rows[8].amount, rows[8].percent], ['其他', 20, 20])
  assert.equal(rows[0].percent, 10)
  assert.notEqual(rows[0].color, rows[1].color)
  assert.deepEqual(compositionRows(undefined), [])
})

test('dailySummary 只保留有收支的天并排序', () => {
  const rows = dailySummary([
    { period: '2026-10-05', income: 0, expense: 3 }, { period: '2026-10-02', income: 9, expense: 0 }, { period: '2026-10-03', income: 0, expense: 0 },
  ])
  assert.deepEqual(rows.map((r) => r.day), [2, 5])
})
