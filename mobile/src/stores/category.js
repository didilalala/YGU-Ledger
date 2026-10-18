/**
 * 分类缓存。对应原项目 hooks/useCategories.ts（React Query 缓存 → Pinia）。
 */
import { defineStore } from 'pinia'
import { categoryApi } from '@/api'

export const useCategoryStore = defineStore('category', {
  state: () => ({
    list: [],
    loaded: false,
  }),

  getters: {
    expense: (state) => state.list.filter((c) => c.type === 'expense'),
    income: (state) => state.list.filter((c) => c.type === 'income'),
  },

  actions: {
    /** @param {boolean} [force] 为 true 时忽略缓存重新拉取 */
    async load(force = false) {
      if (this.loaded && !force) return this.list
      this.list = await categoryApi.list()
      this.loaded = true
      return this.list
    },
  },
})
