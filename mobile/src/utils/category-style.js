/**
 * 分类色块的配色（Claymorphism 马卡龙粉彩）。
 * 原项目对常用分类写死了颜色；用户自定义分类没有预设，这里按名称稳定地从调色板里选一个，
 * 保证同一个分类每次都是同一种颜色。
 */
const FIXED = {
  餐饮: '#FFD86B', // 奶黄
  交通: '#8FC0FA', // 天蓝
  购物: '#FF9EC4', // 粉
  娱乐: '#B79CF5', // 薰衣草
  医疗: '#FF8A80', // 珊瑚
  教育: '#FFAE7A', // 杏橙
  住房: '#7FD8E8', // 冰青
  工资: '#7ADBB0', // 薄荷
  奖金: '#B6E57A', // 青柠
  投资: '#7ADBB0',
  兼职: '#7FD8E8',
}
const PALETTE = ['#FFD86B', '#8FC0FA', '#FF9EC4', '#B79CF5', '#FFAE7A', '#7FD8E8', '#7ADBB0', '#B6E57A']
const UNCATEGORIZED = '#E8E2F8'

export function categoryColor(name) {
  if (!name) return UNCATEGORIZED
  if (FIXED[name]) return FIXED[name]
  let hash = 0
  for (const ch of name) hash = (hash * 31 + ch.codePointAt(0)) >>> 0
  return PALETTE[hash % PALETTE.length]
}

/** 默认图标：账单没有分类、或分类没有设置图标时用 */
export const fallbackIcon = (type) => (type === 'income' ? '💰' : '📝')
