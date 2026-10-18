/**
 * 标签输入 ↔ 数组。限制与后端 BillSerializer.tags 一致：每个标签最长 30 个字符。
 */
export const MAX_TAGS = 5
export const MAX_TAG_LENGTH = 30

/** "餐饮, 聚餐　朋友、聚餐" → ['餐饮', '聚餐', '朋友']。支持中英文逗号、顿号、空白分隔；去重并保持顺序 */
export function parseTags(input) {
  const seen = new Set()
  const tags = []
  for (const part of String(input ?? '').split(/[,，、\s]+/)) {
    const tag = part.trim().slice(0, MAX_TAG_LENGTH)
    if (tag && !seen.has(tag)) {
      seen.add(tag)
      tags.push(tag)
    }
  }
  return tags.slice(0, MAX_TAGS)
}

export const formatTags = (tags) => (tags || []).join(' ')
