<template>
  <view>
    <view class="sub-seg"><ln-segment v-model="sub" :options="OPTIONS" @change="resetJump" /></view>
    <daily-view v-if="sub === 'daily'" :key="`d-${dailyKey}`" ref="daily" :initial-year="jump.year" :initial-month0="jump.month0"
      :initial-day="jump.day" />
    <monthly-view v-else-if="sub === 'monthly'" :key="`m-${monthlyKey}`" ref="monthly" :initial-year="jump.year"
      :initial-month="jump.month" @jump-daily="toDaily" />
    <yearly-view v-else ref="yearly" @jump-monthly="toMonthly" />
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import DailyView from './daily-view.vue'
import MonthlyView from './monthly-view.vue'
import YearlyView from './yearly-view.vue'

/** 收支页签：日 / 月 / 年三个子视图，下一级可以跳转到上一级（月 → 日，年 → 月），对应原项目 IncomeExpenseTab */
const OPTIONS = [
  { value: 'daily', label: '日收支' },
  { value: 'monthly', label: '月收支' },
  { value: 'yearly', label: '年收支' },
]
const sub = ref('daily')
const jump = reactive({ year: null, month0: null, month: null, day: '' })
// 跳转时要让目标视图按新的初始值重新创建
const dailyKey = ref(0)
const monthlyKey = ref(0)
const daily = ref(null)
const monthly = ref(null)
const yearly = ref(null)

// 手动切换子页签时回到默认的"当前周期"，不沿用上一次跳转带来的年月
function resetJump() {
  Object.assign(jump, { year: null, month0: null, month: null, day: '' })
}

function toDaily(year, month0, day) {
  Object.assign(jump, { year, month0, day })
  dailyKey.value++
  sub.value = 'daily'
}
function toMonthly(year, month) {
  Object.assign(jump, { year, month })
  monthlyKey.value++
  sub.value = 'monthly'
}

defineExpose({ refresh: () => (daily.value || monthly.value || yearly.value)?.refresh?.() })
</script>

<style lang="scss" scoped>
.sub-seg {
  padding: 0 32rpx 32rpx;
}
</style>
