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
