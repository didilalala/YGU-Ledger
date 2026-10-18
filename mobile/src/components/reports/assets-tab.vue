<template>
  <view>
    <!-- 净资产：蓝色主卡 -->
    <view class="balance-card">
      <text class="b-label">净资产（收入 - 支出）</text>
      <text class="b-amount">¥{{ net.toFixed(2) }}</text>
      <view class="b-row">
        <view class="b-item">
          <text class="b-item-label">总收入</text>
          <text class="b-item-value income-c">¥{{ stats.totalIncome.toFixed(2) }}</text>
        </view>
        <view class="b-divider" />
        <view class="b-item">
          <text class="b-item-label">总支出</text>
          <text class="b-item-value expense-c">¥{{ stats.totalExpense.toFixed(2) }}</text>
        </view>
      </view>
    </view>

    <!-- 资产变动趋势 -->
    <view class="panel">
      <view class="panel-head">
        <text class="panel-title">资产变动趋势</text>
        <text class="panel-range mono">{{ rangeText }}</text>
      </view>
      <ln-chart v-if="hasTrend" type="area" :series="trendSeries" :categories="trend.categories" :width-rpx="590"
        :height-rpx="440" />
      <view v-else class="empty-tip">暂无数据</view>
    </view>

    <!-- 支出 / 收入构成 -->
    <view class="panel">
      <view class="panel-head">
        <text class="panel-title">近12月{{ kind === 'expense' ? '支出' : '收入' }}类型构成</text>
        <text class="panel-range mono">{{ rangeText }}</text>
      </view>
      <view class="kind-switch">
        <text :class="['kind', { on: kind === 'expense' }]" @click="kind = 'expense'">支出</text>
        <text :class="['kind', { on: kind === 'income' }]" @click="kind = 'income'">收入</text>
      </view>
      <view v-if="rows.length" class="comp">
        <ln-chart type="ring" :series="pieSeries" :center="{ title: '¥' + Math.round(compTotal), subtitle: '总计' }"
          :width-rpx="290" :height-rpx="290" />
        <view class="legend">
          <view v-for="r in rows" :key="r.name" class="legend-row">
            <view class="dot" :style="{ background: r.color }" />
            <text class="l-icon">{{ r.icon }}</text>
            <text class="l-name">{{ r.name }}</text>
            <text class="l-amount mono">¥{{ Math.round(r.amount) }}</text>
            <text class="l-pct mono">{{ r.percent }}%</text>
          </view>
        </view>
      </view>
      <view v-else class="empty-tip">暂无{{ kind === 'expense' ? '支出' : '收入' }}</view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { billApi } from '@/api'
import LnChart from '@/components/ln-chart/ln-chart.vue'
import { buildPieSeries } from '@/utils/chart'
import { compositionRows, cumulativeNet, lastMonths, rangeOfMonths, trendToMap } from '@/utils/report'

const months = lastMonths(12)
const stats = ref({ totalIncome: 0, totalExpense: 0, expenseByCategory: [], incomeByCategory: [], trend: [] })
const kind = ref('expense')

const net = computed(() => stats.value.totalIncome - stats.value.totalExpense)
const rangeText = `${months[0].year}.${months[0].month} – ${months[11].year}.${months[11].month}`

const trend = computed(() => cumulativeNet(months, trendToMap(stats.value.trend)))
const hasTrend = computed(() => stats.value.trend.length > 0)
const trendSeries = computed(() => [{ name: '净资产', data: trend.value.values, color: '#3B82F6' }])

const items = computed(() => (kind.value === 'expense' ? stats.value.expenseByCategory : stats.value.incomeByCategory))
const rows = computed(() => compositionRows(items.value))
const pieSeries = computed(() => buildPieSeries(items.value))
const compTotal = computed(() => rows.value.reduce((sum, r) => sum + r.amount, 0))

async function load() {
  try {
    stats.value = await billApi.statistics({ ...rangeOfMonths(months), granularity: 'monthly' })
  } catch (e) { /* 请求层已提示 */ }
}
load()

defineExpose({ refresh: load })
</script>

<style lang="scss" scoped>
.balance-card {
  padding: 40rpx;
  margin: 0 32rpx 40rpx;
  color: #fff;
  background: $ln-primary;
  @include brutal-box($ln-r-lg, $ln-bw-thick);
}
.b-label {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
}
.b-amount {
  display: block;
  margin: 16rpx 0 32rpx;
  font-size: 80rpx;
  font-weight: 900;
  letter-spacing: -2rpx;
}
.b-row {
  display: flex;
  align-items: center;
}
.b-item {
  flex: 1;
  padding: 0 8rpx;
}
.b-item-label {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
}
.b-item-value {
  display: block;
  margin-top: 8rpx;
  font-size: 44rpx;
  font-weight: 900;
}
.income-c {
  color: #4ade80;
}
.expense-c {
  color: #f87171;
}
.b-divider {
  width: $ln-bw-thin;
  height: 80rpx;
  margin: 0 32rpx;
  background: rgba(255, 255, 255, 0.3);
}
.panel {
  padding: 32rpx;
  margin: 0 32rpx 40rpx;
  background: $ln-card;
  @include brutal-box($ln-r-lg, $ln-bw-thick);
}
.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 24rpx;
}
.panel-title {
  font-size: 34rpx;
  font-weight: 800;
  white-space: nowrap;
}
.panel-range {
  font-size: 22rpx;
  white-space: nowrap;
  color: $ln-text-secondary;
}
.kind-switch {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
}
.kind {
  padding: 6rpx 28rpx;
  font-size: 26rpx;
  font-weight: 800;
  color: $ln-text-secondary;
  border: $ln-bw-thin solid transparent;
  border-radius: $ln-r-sm;
  &.on {
    color: $ln-text;
    background: $ln-accent;
    border-color: $ln-stroke;
  }
}
.comp {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.legend {
  flex: 1;
  min-width: 0;
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  padding: 10rpx 0;
  font-size: 26rpx;
}
.dot {
  flex-shrink: 0;
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
}
.l-icon {
  font-size: 30rpx;
}
.l-name {
  flex: 1;
  min-width: 0;
  font-weight: 700;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.l-amount {
  font-weight: 800;
}
.l-pct {
  min-width: 70rpx;
  text-align: right;
  color: $ln-text-secondary;
}
</style>
