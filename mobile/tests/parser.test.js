// 运行：npm test（Node 内置 test runner，无需额外依赖）
// 下面的通知文案是示意样本，需替换/补充为真机抓到的真实通知
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createDeduplicator, PACKAGES, parseNotification } from '../src/services/notification/parser.js'

test('微信支付消费', () => {
  const bill = parseNotification({ pkg: PACKAGES.WECHAT, title: '微信支付', text: '已支付¥23.50', postTime: Date.UTC(2026, 9, 18, 4) })
  assert.equal(bill.amount, 23.5)
  assert.equal(bill.type, 'expense')
  assert.equal(bill.source, 'notification')
})

test('微信收款', () => {
  const bill = parseNotification({ pkg: PACKAGES.WECHAT, title: '微信支付', text: '微信支付收款100.00元' })
  assert.equal(bill.type, 'income')
  assert.equal(bill.amount, 100)
})

test('支付宝付款', () => {
  const bill = parseNotification({ pkg: PACKAGES.ALIPAY, title: '支付宝', text: '你已成功付款12.80元' })
  assert.equal(bill.amount, 12.8)
  assert.equal(bill.type, 'expense')
})

test('无关通知与其他应用返回 null', () => {
  assert.equal(parseNotification({ pkg: PACKAGES.WECHAT, title: '张三', text: '晚上吃饭吗' }), null)
  assert.equal(parseNotification({ pkg: 'com.other.app', title: '支付', text: '支付10元' }), null)
})

test('窗口期内重复通知被去重', () => {
  const isDup = createDeduplicator(1000)
  const bill = { type: 'expense', amount: 10 }
  assert.equal(isDup(bill, 0), false)
  assert.equal(isDup(bill, 500), true)
  assert.equal(isDup(bill, 2000), false)
})

import { describeBill, toBillPayload } from '../src/services/notification/payload.js'
import { createSerialQueue } from '../src/services/notification/serial-queue.js'

test('describeBill / toBillPayload', () => {
  const bill = parseNotification({ pkg: PACKAGES.WECHAT, title: '微信支付', text: '已支付¥23.50', postTime: new Date(2026, 9, 18, 12).getTime() })
  assert.equal(describeBill(bill), '支出 ¥23.50\n微信支付\n2026-10-18')
  const payload = toBillPayload(bill)
  assert.deepEqual(Object.keys(payload).sort(), ['amount', 'date', 'description', 'notes', 'source', 'type'])
  assert.equal(payload.source, 'notification')
  assert.equal(payload.notes, bill.raw)
  assert.equal(describeBill({ ...bill, type: 'income', amount: 5 }).startsWith('收入 ¥5.00'), true)
})

test('串行队列：任务按顺序依次执行，不会并发', async () => {
  const queue = createSerialQueue()
  const log = []
  let running = 0
  let maxRunning = 0
  const task = (name, ms) => async () => {
    running++
    maxRunning = Math.max(maxRunning, running)
    log.push(`start ${name}`)
    await new Promise((r) => setTimeout(r, ms))
    log.push(`end ${name}`)
    running--
    return name
  }
  const results = await Promise.all([queue.push(task('a', 20)), queue.push(task('b', 5)), queue.push(task('c', 1))])
  assert.deepEqual(results, ['a', 'b', 'c'])
  assert.deepEqual(log, ['start a', 'end a', 'start b', 'end b', 'start c', 'end c'])
  assert.equal(maxRunning, 1)
})

test('串行队列：某个任务失败不影响后面的任务，且自己能拿到错误', async () => {
  const queue = createSerialQueue()
  const failing = queue.push(async () => { throw new Error('boom') })
  const after = queue.push(async () => 'ok')
  await assert.rejects(failing, /boom/)
  assert.equal(await after, 'ok')
  assert.equal(queue.size, 0)
})
