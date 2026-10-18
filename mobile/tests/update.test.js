import test from 'node:test'
import assert from 'node:assert/strict'

import { describeUpdate } from '../src/utils/update-info.js'

test('没有更新 / 数据缺失时返回 null', () => {
  assert.equal(describeUpdate(null), null)
  assert.equal(describeUpdate({ hasUpdate: false, latest: null }), null)
  assert.equal(describeUpdate({ hasUpdate: true, latest: null }), null)
})

test('有更新时生成弹窗内容', () => {
  const info = describeUpdate({
    hasUpdate: true, forceUpdate: false,
    latest: { version: '1.2.0', updateLog: ' 修复若干问题 ', downloadUrl: 'https://x/y.apk' },
  })
  assert.deepEqual(info, { title: '发现新版本 1.2.0', content: '修复若干问题', force: false, url: 'https://x/y.apk' })
})

test('强制更新、更新日志为空', () => {
  const info = describeUpdate({ hasUpdate: true, forceUpdate: true, latest: { version: '2.0.0', updateLog: '', downloadUrl: 'u' } })
  assert.equal(info.force, true)
  assert.equal(info.content, '优化体验，修复问题')
})
