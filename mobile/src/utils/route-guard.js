/**
 * 路由守卫：未登录时访问需要登录的页面，跳转到登录页。
 * uni-app 没有统一的路由钩子，通过拦截各跳转 API 实现。
 */
import { storage, STORAGE_KEYS } from './storage'

const PUBLIC_PAGES = ['/pages/auth/login', '/pages/auth/register']

function needLogin(url) {
  const path = url.split('?')[0]
  return !PUBLIC_PAGES.includes(path) && !storage.get(STORAGE_KEYS.TOKEN)
}

export function setupRouteGuard() {
  ;['navigateTo', 'redirectTo', 'reLaunch', 'switchTab'].forEach((method) => {
    uni.addInterceptor(method, {
      invoke(args) {
        if (needLogin(args.url)) {
          uni.reLaunch({ url: '/pages/auth/login' })
          return false
        }
        return true
      },
    })
  })
}
