/**
 * 本地存储封装。对应原项目 utils/storage.ts（AsyncStorage → uni storage）。
 */
export const STORAGE_KEYS = {
  TOKEN: 'litenote_token',
  USER: 'litenote_user',
  OPEN_SESSION: 'litenote_open_session', // 会话页 → 聊天页（tabBar 页面不能带参数跳转）
}

export const storage = {
  get(key, defaultValue = null) {
    try {
      const value = uni.getStorageSync(key)
      return value === '' || value === undefined ? defaultValue : value
    } catch (e) {
      return defaultValue
    }
  },
  set(key, value) {
    try {
      uni.setStorageSync(key, value)
    } catch (e) {
      console.warn('[storage] 写入失败', key, e)
    }
  },
  remove(key) {
    try {
      uni.removeStorageSync(key)
    } catch (e) {
      // 忽略
    }
  },
}
