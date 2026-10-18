/**
 * 所有后端接口集中在这里，字段名以后端 Swagger（/api/docs）为准。
 * 不使用 TypeScript，所以页面里不要直接拼 URL，统一调用这里的函数。
 */
import { http, upload } from './http'

export const authApi = {
  register: (data) => http.post('/auth/register', data),
  login: (data) => http.post('/auth/login', data),
  profile: () => http.get('/auth/profile'),
  updateProfile: (data) => http.patch('/auth/profile', data),
  changePassword: (data) => http.patch('/auth/password', data),
  uploadAvatar: (filePath) => upload('/auth/avatar', filePath),
}

export const billApi = {
  /** @param {{page?, limit?, type?, categoryId?, startDate?, endDate?, orderBy?, orderDirection?}} params */
  list: (params) => http.get('/bills', params),
  detail: (id) => http.get(`/bills/${id}`),
  create: (data) => http.post('/bills', data),
  update: (id, data) => http.patch(`/bills/${id}`, data),
  remove: (id) => http.delete(`/bills/${id}`),
  /** @param {{startDate?, endDate?, granularity?: 'daily'|'monthly'}} params */
  statistics: (params) => http.get('/bills/statistics', params),
}

export const categoryApi = {
  /** @param {'income'|'expense'} [type] */
  list: (type) => http.get('/categories', { type }),
  create: (data) => http.post('/categories', data),
  update: (id, data) => http.patch(`/categories/${id}`, data),
  remove: (id) => http.delete(`/categories/${id}`),
}

export const accountApi = {
  list: () => http.get('/accounts'),
  create: (data) => http.post('/accounts', data),
  update: (id, data) => http.patch(`/accounts/${id}`, data),
  remove: (id) => http.delete(`/accounts/${id}`),
  balance: () => http.get('/accounts/balance'),
}

export const budgetApi = {
  list: () => http.get('/budgets'),
  create: (data) => http.post('/budgets', data),
  update: (id, data) => http.patch(`/budgets/${id}`, data),
  remove: (id) => http.delete(`/budgets/${id}`),
  progress: () => http.get('/budgets/progress'),
}

export const goalApi = {
  list: () => http.get('/financial-goals'),
  create: (data) => http.post('/financial-goals', data),
  update: (id, data) => http.patch(`/financial-goals/${id}`, data),
  remove: (id) => http.delete(`/financial-goals/${id}`),
  progress: () => http.get('/financial-goals/progress'),
}

export const aiApi = {
  configs: () => http.get('/ai/configs'),
  createConfig: (data) => http.post('/ai/configs', data),
  updateConfig: (id, data) => http.patch(`/ai/configs/${id}`, data),
  removeConfig: (id) => http.delete(`/ai/configs/${id}`),
  setDefault: (id) => http.post(`/ai/configs/${id}/set-default`),
  testConfig: (id) => http.post(`/ai/configs/${id}/test`),

  /** @param {{message, sessionId?, aiConfigId?, images?: string[]}} data */
  send: (data) => http.post('/ai/chat/send', data),
  sessions: (params) => http.get('/ai/chat/sessions', params),
  session: (id) => http.get(`/ai/chat/sessions/${id}`),
  renameSession: (id, title) => http.patch(`/ai/chat/sessions/${id}`, { title }),
  togglePin: (id) => http.post(`/ai/chat/sessions/${id}/toggle-pin`),
  removeSession: (id) => http.delete(`/ai/chat/sessions/${id}`),

  /** @param {string} audio base64 */
  transcribe: (audio, mimeType) => http.post('/ai/asr/transcribe', { audio, mimeType }),
}

export const versionApi = {
  check: (versionCode, platform = 'android') => http.get('/app-version/check', { versionCode, platform }),
}
