<template>
  <view>
    <view class="card mode">
      <uni-segmented-control :current="mode === 'month' ? 0 : 1" :values="['月', '年']" style-type="text"
        @clickItem="(e) => switchMode(e.currentIndex === 0 ? 'month' : 'year')" />
    </view>

    <view class="card period">
      <text class="arrow" @click="shift(-1)">‹</text>
      <text class="month">{{ periodLabel }}</text>
      <text class="arrow" @click="shift(1)">›</text>
    </view>

    <view class="card totals">
      <view class="col"><text class="muted">收入</text><text class="income">{{ formatMoney(stats.totalIncome) }}</text></view>
      <view class="col"><text class="muted">支出</text><text class="expense">{{ formatMoney(stats.totalExpense) }}</text></view>
      <view class="col"><text class="muted">结余</text><text>{{ formatMoney(stats.balance) }}</text></view>
    </view>

    <view class="card">
      <text class="title">支出构成</text>
      <ln-chart v-if="pieSeries[0].data.length" type="ring" :series="pieSeries" />
      <view v-for="c in stats.expenseByCategory" :key="c.categoryId ?? 'none'" class="bar-row">
        <text class="bar-label">{{ c.categoryIcon }} {{ c.categoryName }}</text>
        <view class="bar-track"><view class="bar" :style="{ width: c.percentage + '%' }" /></view>
        <text class="amount muted">{{ formatMoney(c.amount) }}</text>
      </view>
      <view v-if="!stats.expenseByCategory?.length" class="muted empty">{{ mode === 'month' ? '本月' : '本年' }}暂无支出</view>
    </view>

    <view class="card">
      <text class="title">{{ mode === 'month' ? '每日收支' : '每月收支' }}</text>
      <ln-chart v-if="trendHasData" :type="mode === 'month' ? 'line' : 'column'" :series="trendSeries"
        :categories="trend.categories" />
      <view v-else class="muted empty">暂无数据</view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { billApi } from '@/api'
import LnChart from '@/components/ln-chart/ln-chart.vue'
import { buildPieSeries, buildTrendSeries, fillDailyTrend, fillMonthlyTrend, hasData } from '@/utils/chart'
import { formatMoney, monthRange, toDateString } from '@/utils/format'

const mode = ref('month') // month | year
const current = ref(new Date())
const stats = ref({ totalIncome: 0, totalExpense: 0, balance: 0, expenseByCategory: [], trend: [] })

const year = computed(() => current.value.getFullYear())
const month = computed(() => current.value.getMonth() + 1)
const periodLabel = computed(() => (mode.value === 'month' ? `${year.value} 年 ${month.value} 月` : `${year.value} 年`))

const pieSeries = computed(() => buildPieSeries(stats.value.expenseByCategory))
const trend = computed(() => (mode.value === 'month'
  ? fillDailyTrend(stats.value.trend, year.value, month.value)
  : fillMonthlyTrend(stats.value.trend, year.value)))
const trendSeries = computed(() => buildTrendSeries(trend.value))
const trendHasData = computed(() => hasData(trend.value))

let seq = 0 // 连续切换月份时，丢弃过期的响应

async function load() {
  const mine = ++seq
  const range = mode.value === 'month'
    ? monthRange(current.value)
    : { startDate: toDateString(new Date(year.value, 0, 1)), endDate: toDateString(new Date(year.value, 11, 31)) }
  const data = await billApi.statistics({ ...range, granularity: mode.value === 'month' ? 'daily' : 'monthly' })
  if (mine === seq) stats.value = data
}

function switchMode(next) {
  if (next === mode.value) return
  mode.value = next
  load().catch(() => {})
}

function shift(delta) {
  const d = current.value
  current.value = mode.value === 'month'
    ? new Date(d.getFullYear(), d.getMonth() + delta, 1)
    : new Date(d.getFullYear() + delta, d.getMonth(), 1)
  load().catch(() => {})
}

onShow(() => load().catch(() => {}))
</script>

<style lang="scss" scoped>
.mode {
  padding: 8rpx 32rpx;
}
.period {
  display: flex;
  justify-content: space-between;
  font-size: 36rpx;
}
.arrow {
  padding: 0 24rpx;
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
  display: block;
  font-weight: 600;
  margin-bottom: 8rpx;
}
.bar-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 20rpx;
}
.bar-label {
  width: 180rpx;
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
.amount {
  min-width: 120rpx;
  text-align: right;
}
.empty {
  text-align: center;
  padding: 48rpx 0;
}
</style>
