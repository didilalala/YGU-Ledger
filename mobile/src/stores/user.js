/**
 * 登录态。对应原项目 providers/AuthProvider.tsx。
 */
import { defineStore } from 'pinia'
import { authApi } from '@/api'
import { storage, STORAGE_KEYS } from '@/utils/storage'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: storage.get(STORAGE_KEYS.TOKEN, ''),
    user: storage.get(STORAGE_KEYS.USER, null),
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    displayName: (state) => state.user?.nickname || state.user?.username || '',
  },

  actions: {
    _save({ user, token }) {
      this.user = user
      this.token = token
      storage.set(STORAGE_KEYS.USER, user)
      storage.set(STORAGE_KEYS.TOKEN, token)
    },

    async login(username, password) {
      this._save(await authApi.login({ username, password }))
    },

    async register(form) {
      this._save(await authApi.register(form))
    },

    async refreshProfile() {
      this.user = await authApi.profile()
      storage.set(STORAGE_KEYS.USER, this.user)
    },

    logout() {
      this.user = null
      this.token = ''
      storage.remove(STORAGE_KEYS.USER)
      storage.remove(STORAGE_KEYS.TOKEN)
      uni.reLaunch({ url: '/pages/auth/login' })
    },
  },
})
