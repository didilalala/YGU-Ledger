<template>
  <view>
    <period-nav :title="`${year}年`" :disable-next="year >= now.getFullYear()" @prev="shift(-1)" @next="shift(1)" />
    <view class="grid">
      <view v-for="c in cells" :key="c.key" class="slot">
        <grid-cell :label="c.label" :income="c.income" :expense="c.expense" :selected="selectedMonth === c.month"
          :current="c.isCurrent" :disabled="c.isFuture" @press="toggle(c.month)" />
      </view>
    </view>

    <view v-if="selectedMonth" class="detail">
      <text class="detail-title">{{ year }}年{{ selectedMonth }}月 每日收支</text>
      <view v-for="d in days" :key="d.date" class="row" @click="$emit('jump-daily', year, selectedMonth - 1, d.date)">
        <text class="row-day">{{ d.day }}日</text>
        <text class="income mono">{{ d.income > 0 ? '+' + d.income.toFixed(2) : '' }}</text>
        <text class="expense mono">{{ d.expense > 0 ? '-' + d.expense.toFixed(2) : '' }}</text>
        <ln-icon name="chevron-right" :size="32" color="#A3A3A3" />
      </view>
      <view v-if="!days.length" class="empty-tip">该月暂无记录</view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { billApi } from '@/api'
import { monthRange, toDateString } from '@/utils/format'
import { buildMonthCells, dailySummary, trendToMap } from '@/utils/report'
import GridCell from './grid-cell.vue'
import PeriodNav from './period-nav.vue'

const props = defineProps({
  initialYear: { type: Number, default: null },
  initialMonth: { type: Number, default: null }, // 1 起始
})
defineEmits(['jump-daily'])

const now = new Date()
const year = ref(props.initialYear ?? now.getFullYear())
const selectedMonth = ref(props.initialMonth || null)
const monthlyMap = ref({})
const days = ref([])

const cells = computed(() => buildMonthCells(year.value, monthlyMap.value, now))

let seq = 0
async function loadYear() {
  const mine = ++seq
  try {
    const stats = await billApi.statistics({
      startDate: toDateString(new Date(year.value, 0, 1)), endDate: toDateString(new Date(year.value, 11, 31)),
      granularity: 'monthly',
    })
    if (mine === seq) monthlyMap.value = trendToMap(stats.trend)
  } catch (e) { /* 请求层已提示 */ }
}

let daySeq = 0
async function loadDays() {
  if (!selectedMonth.value) return
  const mine = ++daySeq
  try {
    const stats = await billApi.statistics({ ...monthRange(new Date(year.value, selectedMonth.value - 1, 1)), granularity: 'daily' })
    if (mine === daySeq) days.value = dailySummary(stats.trend)
  } catch (e) { /* 请求层已提示 */ }
}

function shift(delta) {
  year.value += delta
  selectedMonth.value = null
  days.value = []
}
function toggle(month) {
  selectedMonth.value = selectedMonth.value === month ? null : month
  days.value = []
}

watch(year, loadYear, { immediate: true })
watch([selectedMonth, year], loadDays, { immediate: true })

defineExpose({ refresh: () => Promise.all([loadYear(), loadDays()]) })
</script>

<style lang="scss" scoped>
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
  &:active {
    background: $ln-bg;
  }
}
.row-day {
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
