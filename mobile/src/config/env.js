/**
 * 环境配置。通过 .env.development / .env.production 中的 VITE_ 变量覆盖。
 * - H5 开发：走 vite 代理，baseURL 用相对路径 /api
 * - App 真机：必须填电脑或服务器的局域网/公网地址，如 http://192.168.1.10/api
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export const REQUEST_TIMEOUT = 30000
