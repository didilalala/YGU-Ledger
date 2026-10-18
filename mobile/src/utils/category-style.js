/**
 * 分类色块的配色（Neo-Brutalism 饱和糖果色）。
 * 原项目对常用分类写死了颜色；用户自定义分类没有预设，这里按名称稳定地从调色板里选一个，
 * 保证同一个分类每次都是同一种颜色。
 */
const FIXED = {
  餐饮: '#FACC15', // 明黄
  交通: '#3B82F6', // 蓝
  购物: '#EC4899', // 粉
  娱乐: '#A855F7', // 紫
  医疗: '#EF4444', // 红
  教育: '#F97316', // 橙
  住房: '#06B6D4', // 青
  工资: '#22C55E', // 绿
  奖金: '#84CC16', // 柠檬绿
  投资: '#22C55E',
  兼职: '#06B6D4',
}
const PALETTE = ['#FACC15', '#3B82F6', '#EC4899', '#A855F7', '#F97316', '#06B6D4', '#22C55E', '#84CC16']
const UNCATEGORIZED = '#E5E5E5'

export function categoryColor(name) {
  if (!name) return UNCATEGORIZED
  if (FIXED[name]) return FIXED[name]
  let hash = 0
  for (const ch of name) hash = (hash * 31 + ch.codePointAt(0)) >>> 0
  return PALETTE[hash % PALETTE.length]
}

/** 默认图标：账单没有分类、或分类没有设置图标时用 */
export const fallbackIcon = (type) => (type === 'income' ? '💰' : '📝')
