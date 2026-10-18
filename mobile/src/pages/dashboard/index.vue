<template>
  <view>
    <view class="card summary">
      <text class="muted">本月结余</text>
      <text class="balance">{{ formatMoney(stats.balance) }}</text>
      <view class="row">
        <view class="col">
          <text class="muted">收入</text>
          <text class="income">{{ formatMoney(stats.totalIncome) }}</text>
        </view>
        <view class="col">
          <text class="muted">支出</text>
          <text class="expense">{{ formatMoney(stats.totalExpense) }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>最近账单</text>
        <text class="muted" @click="goBills">全部 ›</text>
      </view>
      <bill-item v-for="bill in recent" :key="bill.id" :bill="bill" @click="goDetail" />
      <view v-if="!recent.length" class="muted empty">还没有账单，点击右下角记一笔</view>
    </view>

    <!-- TODO: 预算卡片、财务目标卡片、快捷入口（对应原项目 DashboardScreen） -->

    <view class="fab" @click="goCreate">＋</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { billApi } from '@/api'
import { formatMoney, monthRange } from '@/utils/format'

const stats = ref({ balance: 0, totalIncome: 0, totalExpense: 0 })
const recent = ref([])

async function load() {
  const [s, list] = await Promise.all([
    billApi.statistics(monthRange()),
    billApi.list({ page: 1, limit: 5 }),
  ])
  stats.value = s
  recent.value = list.items
}

// 从记账页返回时刷新
onShow(() => load().catch(() => {}))

const goCreate = () => uni.navigateTo({ url: '/pages/bills/create' })
const goBills = () => uni.switchTab({ url: '/pages/bills/index' })
const goDetail = (bill) => uni.navigateTo({ url: `/pages/bills/detail?id=${bill.id}` })
</script>

<style lang="scss" scoped>
.summary {
  background: $ln-primary;
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  .muted,
  .income,
  .expense {
    color: rgba(255, 255, 255, 0.85);
  }
}
.balance {
  font-size: 64rpx;
  font-weight: 700;
}
.row {
  display: flex;
  margin-top: 16rpx;
}
.col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.section-title {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
  margin-bottom: 8rpx;
}
.empty {
  padding: 48rpx 0;
  text-align: center;
}
.fab {
  position: fixed;
  right: 48rpx;
  bottom: calc(48rpx + var(--window-bottom));
  width: 112rpx;
  height: 112rpx;
  border-radius: 50%;
  background: $ln-primary;
  color: #fff;
  font-size: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(79, 110, 247, 0.4);
}
</style>
