<template>
  <view>
    <view v-for="b in budgets" :key="b.id" :class="['card', { off: !b.isActive }]" @click="edit(b.id)">
      <view class="row">
        <text class="name">{{ categoryLabel(b) }} · {{ b.name }}</text>
        <text v-if="!b.isActive" class="muted">已停用</text>
        <text v-else :class="{ expense: b.isOverBudget }">{{ formatMoney(b.spent) }} / {{ formatMoney(b.amount) }}</text>
      </view>
      <template v-if="b.isActive">
        <progress :percent="Math.min(b.percentage, 100)" :activeColor="b.isAlert ? '#e5484d' : '#4f6ef7'" stroke-width="6" />
        <text class="muted">{{ b.period === 'monthly' ? '本月' : '今年' }}剩余 {{ formatMoney(b.remaining) }}</text>
      </template>
      <text v-else class="muted">{{ formatMoney(b.amount) }} / {{ b.period === 'monthly' ? '每月' : '每年' }}</text>
    </view>
    <view v-if="loaded && !budgets.length" class="card muted empty">还没有设置预算</view>
    <view class="form-actions">
      <button class="primary" @click="edit()">新建预算</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { budgetApi } from '@/api'
import { useCategoryStore } from '@/stores/category'
import { formatMoney } from '@/utils/format'

const categoryStore = useCategoryStore()
const budgets = ref([])
const loaded = ref(false)

onShow(async () => {
  // progress 只包含启用的预算，停用的要从 list 补上，否则无法重新启用
  const [all, progress] = await Promise.all([budgetApi.list(), budgetApi.progress(), categoryStore.load()])
  const byId = new Map(progress.map((p) => [p.id, p]))
  budgets.value = all.map((b) => byId.get(b.id) || b)
  loaded.value = true
})

function categoryLabel(b) {
  const c = b.categoryId && categoryStore.list.find((x) => x.id === b.categoryId)
  return c ? `${c.icon || ''}${c.name}` : '总预算'
}

const edit = (id) => uni.navigateTo({ url: `/pages/budget/edit${id ? `?id=${id}` : ''}` })
</script>

<style lang="scss" scoped>
.row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16rpx;
}
.name {
  font-weight: 600;
}
.off {
  opacity: 0.6;
}
.empty {
  text-align: center;
}
</style>
