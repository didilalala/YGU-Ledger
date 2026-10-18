<template>
  <view>
    <view class="card period">
      <text @click="shiftMonth(-1)">‹</text>
      <text class="month">{{ monthLabel }}</text>
      <text @click="shiftMonth(1)">›</text>
    </view>

    <view class="card totals">
      <view class="col"><text class="muted">收入</text><text class="income">{{ formatMoney(stats.totalIncome) }}</text></view>
      <view class="col"><text class="muted">支出</text><text class="expense">{{ formatMoney(stats.totalExpense) }}</text></view>
      <view class="col"><text class="muted">结余</text><text>{{ formatMoney(stats.balance) }}</text></view>
    </view>

    <view class="card">
      <text class="title">支出分类</text>
      <!-- TODO: 用 uCharts 画饼图 / 趋势折线图（对应原项目 components/charts、reports/*） -->
      <view v-for="c in stats.expenseByCategory" :key="c.categoryId ?? 'none'" class="bar-row">
        <text class="bar-label">{{ c.categoryIcon }} {{ c.categoryName }}</text>
        <view class="bar-track"><view class="bar" :style="{ width: c.percentage + '%' }" /></view>
        <text class="muted">{{ c.percentage }}%</text>
      </view>
      <view v-if="!stats.expenseByCategory?.length" class="muted empty">本月暂无支出</view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { billApi } from '@/api'
import { formatMoney, monthRange } from '@/utils/format'

const current = ref(new Date())
const stats = ref({ totalIncome: 0, totalExpense: 0, balance: 0, expenseByCategory: [] })

const monthLabel = computed(() => `${current.value.getFullYear()} 年 ${current.value.getMonth() + 1} 月`)

async function load() {
  stats.value = await billApi.statistics({ ...monthRange(current.value), granularity: 'daily' })
}

function shiftMonth(delta) {
  const d = current.value
  current.value = new Date(d.getFullYear(), d.getMonth() + delta, 1)
  load().catch(() => {})
}

onShow(() => load().catch(() => {}))
</script>

<style lang="scss" scoped>
.period {
  display: flex;
  justify-content: space-between;
  font-size: 36rpx;
}
.month {
  font-weight: 600;
}
.totals {
  display: flex;
}
.col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}
.title {
  font-weight: 600;
}
.bar-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 20rpx;
}
.bar-label {
  width: 160rpx;
}
.bar-track {
  flex: 1;
  height: 16rpx;
  background: $ln-bg;
  border-radius: 8rpx;
  overflow: hidden;
}
.bar {
  height: 100%;
  background: $ln-expense;
}
.empty {
  text-align: center;
  padding: 48rpx 0;
}
</style>
