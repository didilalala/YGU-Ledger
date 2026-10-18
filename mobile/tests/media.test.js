import test from 'node:test'
import assert from 'node:assert/strict'
import { fitSize, stripDataUrl } from '../src/utils/media.js'
import { baseMime } from '../src/utils/recorder.js'

test('fitSize 缩小长边并保持比例', () => {
  assert.deepEqual(fitSize(4000, 3000), { width: 1024, height: 768 })
  assert.deepEqual(fitSize(3000, 4000), { width: 768, height: 1024 })
})

test('fitSize 小图不放大', () => {
  assert.deepEqual(fitSize(800, 600), { width: 800, height: 600 })
  assert.deepEqual(fitSize(1024, 1024), { width: 1024, height: 1024 })
})

test('fitSize 取不到尺寸时原样返回', () => {
  assert.deepEqual(fitSize(0, 0), { width: 0, height: 0 })
})

test('stripDataUrl 去掉 data URL 前缀', () => {
  assert.equal(stripDataUrl('data:audio/aac;base64,QUJD'), 'QUJD')
  assert.equal(stripDataUrl('QUJD'), 'QUJD')
})

test('baseMime 去掉 codecs 参数', () => {
  assert.equal(baseMime('audio/webm;codecs=opus'), 'audio/webm')
  assert.equal(baseMime('audio/mp4'), 'audio/mp4')
})
