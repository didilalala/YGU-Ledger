<template>
  <view>
    <period-nav :title="`${year}年${month0 + 1}月`" :disable-next="isNextDisabled" @prev="shift(-1)" @next="shift(1)" />
    <view class="calendar-wrap">
      <calendar-grid :year="year" :month0="month0" :daily-map="dailyMap" :selected="selected" @select="toggle" />
    </view>

    <view v-if="selected" class="detail">
      <view class="detail-head">
        <text class="detail-title">{{ Number(selected.slice(5, 7)) }}月{{ Number(selected.slice(8, 10)) }}日明细</text>
        <view class="day-sum mono">
          <text v-if="dayData.income > 0" class="income">收 +{{ dayData.income.toFixed(2) }}</text>
          <text v-if="dayData.expense > 0" class="expense">支 -{{ dayData.expense.toFixed(2) }}</text>
        </view>
      </view>
      <bill-item v-for="b in bills" :key="b.id" :bill="b" @click="openBill" />
      <view v-if="!loadingBills && !bills.length" class="empty-tip">当天暂无记录</view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { billApi } from '@/api'
import { monthRange } from '@/utils/format'
import { trendToMap } from '@/utils/report'
import CalendarGrid from './calendar-grid.vue'
import PeriodNav from './period-nav.vue'

const props = defineProps({
  initialYear: { type: Number, default: null },
  initialMonth0: { type: Number, default: null },
  initialDay: { type: String, default: '' },
})

const now = new Date()
const year = ref(props.initialYear ?? now.getFullYear())
const month0 = ref(props.initialMonth0 ?? now.getMonth())
const selected = ref(props.initialDay || '')
const dailyMap = ref({})
const bills = ref([])
const loadingBills = ref(false)

const isNextDisabled = computed(() => year.value === now.getFullYear() && month0.value >= now.getMonth())
const dayData = computed(() => dailyMap.value[selected.value] || { income: 0, expense: 0 })

let seq = 0
async function loadMonth() {
  const mine = ++seq
  const range = monthRange(new Date(year.value, month0.value, 1))
  try {
    const stats = await billApi.statistics({ ...range, granularity: 'daily' })
    if (mine === seq) dailyMap.value = trendToMap(stats.trend)
  } catch (e) { /* 请求层已提示 */ }
}

let billSeq = 0
async function loadBills() {
  if (!selected.value) return
  const mine = ++billSeq
  loadingBills.value = true
  try {
    const data = await billApi.list({ page: 1, limit: 50, startDate: selected.value, endDate: selected.value })
    if (mine === billSeq) bills.value = data.items
  } catch (e) { /* 请求层已提示 */ } finally {
    if (mine === billSeq) loadingBills.value = false
  }
}

function shift(delta) {
  const d = new Date(year.value, month0.value + delta, 1)
  year.value = d.getFullYear()
  month0.value = d.getMonth()
  selected.value = ''
  bills.value = []
}

const toggle = (dateStr) => {
  selected.value = selected.value === dateStr ? '' : dateStr
  bills.value = []
}

watch([year, month0], loadMonth, { immediate: true })
watch(selected, loadBills, { immediate: true })

const openBill = (b) => uni.navigateTo({ url: `/pages/bills/detail?id=${b.id}` })

defineExpose({ refresh: () => Promise.all([loadMonth(), loadBills()]) })
</script>

<style lang="scss" scoped>
.calendar-wrap {
  padding: 0 32rpx;
}
.detail {
  padding: 48rpx 32rpx 0;
}
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}
.detail-title {
  font-size: 34rpx;
  font-weight: 800;
}
.day-sum {
  display: flex;
  gap: 24rpx;
  font-size: 26rpx;
  font-weight: 700;
}
</style>
