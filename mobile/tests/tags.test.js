import test from 'node:test'
import assert from 'node:assert/strict'
import { MAX_TAG_LENGTH, MAX_TAGS, formatTags, parseTags } from '../src/utils/tags.js'

test('parseTags 支持多种分隔符并去重', () => {
  assert.deepEqual(parseTags('餐饮, 聚餐　朋友、聚餐，餐饮'), ['餐饮', '聚餐', '朋友'])
  assert.deepEqual(parseTags('a b\tc\nd'), ['a', 'b', 'c', 'd'])
})

test('parseTags 空输入与纯分隔符', () => {
  for (const v of ['', '   ', ',,，、', null, undefined]) assert.deepEqual(parseTags(v), [])
})

test('parseTags 限制数量与单个长度', () => {
  assert.equal(parseTags('1 2 3 4 5 6 7').length, MAX_TAGS)
  assert.equal(parseTags('x'.repeat(100))[0].length, MAX_TAG_LENGTH)
})

test('formatTags 与 parseTags 互逆', () => {
  assert.equal(formatTags(['餐饮', '聚餐']), '餐饮 聚餐')
  assert.deepEqual(parseTags(formatTags(['a', 'b'])), ['a', 'b'])
  assert.equal(formatTags(undefined), '')
})
