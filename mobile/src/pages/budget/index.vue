<template>
  <view>
    <view v-for="b in budgets" :key="b.id" class="card">
      <view class="row">
        <text class="name">{{ b.name }}</text>
        <text :class="{ expense: b.isOverBudget }">{{ formatMoney(b.spent) }} / {{ formatMoney(b.amount) }}</text>
      </view>
      <progress :percent="Math.min(b.percentage, 100)" :activeColor="b.isAlert ? '#e5484d' : '#4f6ef7'" stroke-width="6" />
      <text class="muted">{{ b.period === 'monthly' ? '本月' : '今年' }}剩余 {{ formatMoney(b.remaining) }}</text>
    </view>
    <view v-if="!budgets.length" class="card muted empty">还没有设置预算</view>
    <!-- TODO: 新建/编辑/删除预算表单 -->
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { budgetApi } from '@/api'
import { formatMoney } from '@/utils/format'

const budgets = ref([])

onShow(async () => {
  budgets.value = await budgetApi.progress()
})
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
.empty {
  text-align: center;
}
</style>
