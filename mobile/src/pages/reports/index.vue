<template>
  <view class="page has-tabbar">
    <view class="top-seg"><ln-segment v-model="tab" :options="TABS" /></view>
    <assets-tab v-show="tab === 'assets'" ref="assets" />
    <income-expense-tab v-show="tab === 'income'" ref="income" />
    <ln-tabbar current="reports" />
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import AssetsTab from '@/components/reports/assets-tab.vue'
import IncomeExpenseTab from '@/components/reports/income-expense-tab.vue'

/** 统计页：资产（净资产 / 趋势 / 构成）与收支（日历 / 月 / 年）两个页签，对应原项目 StatisticsScreen */
const TABS = [
  { value: 'assets', label: '资产' },
  { value: 'income', label: '收支' },
]
const tab = ref('assets')
const assets = ref(null)
const income = ref(null)

// 从记账页返回时刷新当前页签的数据
onShow(() => (tab.value === 'assets' ? assets.value : income.value)?.refresh?.())
onPullDownRefresh(async () => {
  await (tab.value === 'assets' ? assets.value : income.value)?.refresh?.()
  uni.stopPullDownRefresh()
})
</script>

<style lang="scss" scoped>
.page {
  padding-top: calc(var(--status-bar-height) + 32rpx);
}
.top-seg {
  padding: 0 32rpx 32rpx;
}
</style>
