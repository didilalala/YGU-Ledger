<template>
  <view>
    <text class="head">近5年收支</text>
    <view class="grid">
      <view v-for="c in cells" :key="c.key" class="slot">
        <grid-cell :label="c.label" :income="c.income" :expense="c.expense" :selected="selectedYear === c.year"
          :current="c.isCurrent" @press="toggle(c.year)" />
      </view>
    </view>

    <view v-if="selectedYear" class="detail">
      <text class="detail-title">{{ selectedYear }}年 每月收支</text>
      <view v-for="m in months" :key="m.key" :class="['row', { disabled: m.isFuture }]"
        @click="!m.isFuture && $emit('jump-monthly', selectedYear, m.month)">
        <text class="row-month">{{ m.label }}</text>
        <text class="income mono">{{ m.income > 0 ? '+' + m.income.toFixed(2) : '' }}</text>
        <text class="expense mono">{{ m.expense > 0 ? '-' + m.expense.toFixed(2) : '' }}</text>
        <ln-icon name="chevron-right" :size="32" color="#A3A3A3" />
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { billApi } from '@/api'
import { toDateString } from '@/utils/format'
import { buildMonthCells, buildYearCells, trendToMap } from '@/utils/report'
import GridCell from './grid-cell.vue'

defineEmits(['jump-monthly'])

const now = new Date()
const monthlyMap = ref({})
const selectedYear = ref(null)

const cells = computed(() => buildYearCells(monthlyMap.value, 5, now))
const months = computed(() => (selectedYear.value ? buildMonthCells(selectedYear.value, monthlyMap.value, now) : []))

const toggle = (year) => { selectedYear.value = selectedYear.value === year ? null : year }

async function load() {
  try {
    const stats = await billApi.statistics({
      startDate: toDateString(new Date(now.getFullYear() - 4, 0, 1)), endDate: toDateString(new Date(now.getFullYear(), 11, 31)),
      granularity: 'monthly',
    })
    monthlyMap.value = trendToMap(stats.trend)
  } catch (e) { /* 请求层已提示 */ }
}
load()

defineExpose({ refresh: load })
</script>

<style lang="scss" scoped>
.head {
  display: block;
  padding: 8rpx 32rpx 32rpx;
  font-size: 40rpx;
  font-weight: 800;
}
.grid {
  display: flex;
  flex-wrap: wrap;
  padding: 0 32rpx;
}
.slot {
  width: 33.3333%;
  height: 150rpx;
  padding: 0 8rpx 16rpx;
}
.detail {
  padding: 40rpx 32rpx 0;
}
.detail-title {
  display: block;
  margin-bottom: 24rpx;
  font-size: 34rpx;
  font-weight: 800;
}
.row {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 24rpx;
  margin: 0 8rpx 20rpx 0;
  background: $ln-card;
  @include brutal-box($ln-r-md, $ln-bw-thin);
  &.disabled {
    opacity: 0.4;
  }
}
.row-month {
  width: 90rpx;
  font-size: 30rpx;
  font-weight: 800;
}
.income,
.expense {
  flex: 1;
  font-size: 26rpx;
  font-weight: 700;
}
</style>
