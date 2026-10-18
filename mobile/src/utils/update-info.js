/**
 * 检查更新结果 → 弹窗内容（纯函数，便于测试）。
 */

/** 接口结果 → 弹窗描述；没有更新返回 null */
export function describeUpdate(result) {
  if (!result?.hasUpdate || !result.latest) return null
  const { version, updateLog, downloadUrl } = result.latest
  return {
    title: `发现新版本 ${version}`,
    content: (updateLog || '').trim() || '优化体验，修复问题',
    force: !!result.forceUpdate,
    url: downloadUrl,
  }
}
