import test from 'node:test'
import assert from 'node:assert/strict'
import { categoryColor, fallbackIcon } from '../src/utils/category-style.js'

test('常用分类使用固定颜色', () => {
  assert.equal(categoryColor('餐饮'), '#FFD86B')
  assert.equal(categoryColor('交通'), '#8FC0FA')
  assert.equal(categoryColor('工资'), '#7ADBB0')
})

test('自定义分类：同名稳定同色，且来自调色板', () => {
  const a = categoryColor('宠物')
  assert.equal(categoryColor('宠物'), a)
  assert.match(a, /^#[0-9A-F]{6}$/)
  const colors = new Set(['宠物', '旅游', '电子器械', '健身', '咖啡', '房贷', '保险', '数码'].map(categoryColor))
  assert.ok(colors.size >= 3, '不同名称应当分散到多种颜色')
})

test('未分类为灰色，默认图标按收支区分', () => {
  assert.equal(categoryColor(null), '#E8E2F8')
  assert.equal(categoryColor(''), '#E8E2F8')
  assert.equal(fallbackIcon('income'), '💰')
  assert.equal(fallbackIcon('expense'), '📝')
})
