/**
 * 检查更新：请求后端、弹窗提示、跳转下载。弹窗内容的生成见 update-info.js。
 */
import { versionApi } from '@/api'
import { describeUpdate } from './update-info'

/** 当前应用的版本码；H5 没有安装包的概念，返回 null */
export function getVersionCode() {
  // #ifdef APP-PLUS
  return Number(uni.getAppBaseInfo().appVersionCode) || 0
  // #endif
  // #ifndef APP-PLUS
  return null
  // #endif
}

/**
 * 检查并提示更新。
 * @param {{silent?: boolean}} options silent=true 时没有更新、检查失败都不打扰用户（启动时自动检查用）
 */
export async function checkUpdate({ silent = false } = {}) {
  const code = getVersionCode()
  if (code === null) {
    if (!silent) uni.showToast({ title: '网页版无需更新', icon: 'none' })
    return
  }
  let info
  try {
    info = describeUpdate(await versionApi.check(code))
  } catch (e) {
    if (!silent) uni.showToast({ title: '检查更新失败', icon: 'none' })
    return
  }
  if (!info) {
    if (!silent) uni.showToast({ title: '已是最新版本', icon: 'none' })
    return
  }
  const { confirm } = await uni.showModal({
    title: info.title,
    content: info.content,
    confirmText: '立即更新',
    showCancel: !info.force, // 强制更新不给"稍后"
  })
  if (confirm) {
    // #ifdef APP-PLUS
    plus.runtime.openURL(info.url) // 交给系统浏览器下载安装包
    // #endif
  } else if (info.force) {
    checkUpdate({ silent })
  }
}
