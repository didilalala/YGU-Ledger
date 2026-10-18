/**
 * 请求封装。对应原项目 services/http.ts（axios → uni.request）。
 *
 * 后端统一返回 { code, message, data, success }：
 * - success 为 true 时 resolve(data)
 * - 否则 reject(Error)，error.code 为状态码；401 时清除登录态并跳转登录页
 */
import { API_BASE_URL, REQUEST_TIMEOUT } from '@/config/env'
import { storage, STORAGE_KEYS } from '@/utils/storage'

const LOGIN_PAGE = '/pages/auth/login'

let redirectingToLogin = false

function handleUnauthorized() {
  storage.remove(STORAGE_KEYS.TOKEN)
  storage.remove(STORAGE_KEYS.USER)
  if (redirectingToLogin) return
  redirectingToLogin = true
  uni.reLaunch({ url: LOGIN_PAGE, complete: () => { redirectingToLogin = false } })
}

function buildQuery(params) {
  if (!params) return ''
  const pairs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
  return pairs.length ? `?${pairs.join('&')}` : ''
}

export function authHeader() {
  const token = storage.get(STORAGE_KEYS.TOKEN)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * @param {object} options
 * @param {string} options.url      相对 API_BASE_URL 的路径，如 /bills
 * @param {'GET'|'POST'|'PATCH'|'DELETE'} [options.method]
 * @param {object} [options.params] 查询参数
 * @param {object} [options.data]   请求体
 * @param {boolean} [options.silent] 为 true 时不自动弹出错误提示
 */
export function request({ url, method = 'GET', params, data, silent = false }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: API_BASE_URL + url + buildQuery(params),
      method,
      data,
      timeout: REQUEST_TIMEOUT,
      header: { 'Content-Type': 'application/json', ...authHeader() },
      success: (res) => {
        const body = res.data || {}
        if (res.statusCode < 400 && body.success !== false) {
          resolve(body.data)
          return
        }
        if (res.statusCode === 401) handleUnauthorized()
        const error = new Error(body.message || `请求失败（${res.statusCode}）`)
        error.code = res.statusCode
        error.details = body.details
        if (!silent && res.statusCode !== 401) uni.showToast({ title: error.message, icon: 'none' })
        reject(error)
      },
      fail: (err) => {
        const error = new Error('网络连接失败，请检查网络')
        error.cause = err
        if (!silent) uni.showToast({ title: error.message, icon: 'none' })
        reject(error)
      },
    })
  })
}

export const http = {
  get: (url, params, opts) => request({ url, method: 'GET', params, ...opts }),
  post: (url, data, opts) => request({ url, method: 'POST', data, ...opts }),
  patch: (url, data, opts) => request({ url, method: 'PATCH', data, ...opts }),
  delete: (url, opts) => request({ url, method: 'DELETE', ...opts }),
}

/**
 * 上传文件（头像等）。uni.uploadFile 返回的 data 是字符串，需要自己解析。
 */
export function upload(url, filePath, name = 'file') {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: API_BASE_URL + url,
      filePath,
      name,
      header: authHeader(),
      success: (res) => {
        let body = {}
        try { body = JSON.parse(res.data) } catch (e) { /* 非 JSON */ }
        if (res.statusCode < 400 && body.success !== false) resolve(body.data)
        else {
          if (res.statusCode === 401) handleUnauthorized()
          reject(new Error(body.message || '上传失败'))
        }
      },
      fail: () => reject(new Error('上传失败，请检查网络')),
    })
  })
}
