<template>
  <view class="page">
    <ln-navbar title="账户管理">
      <template #right><view class="add-btn" @click="edit()"><ln-icon name="plus" :size="40" :stroke="3" /></view></template>
    </ln-navbar>

    <view class="summary">
      <text class="s-label">净资产</text>
      <text class="s-net">¥{{ fixed(balance.netWorth) }}</text>
      <view class="s-row">
        <view class="s-col"><text class="s-sub">总资产</text><text class="s-val income-c">¥{{ fixed(balance.totalAssets) }}</text></view>
        <view class="s-vdiv" />
        <view class="s-col"><text class="s-sub">总负债</text><text class="s-val expense-c">¥{{ fixed(balance.totalLiabilities) }}</text></view>
      </view>
    </view>

    <view class="list">
      <view v-for="a in accounts" :key="a.id" class="account" @click="edit(a.id)">
        <view class="a-icon" :style="{ background: typeColor(a.type) }"><text>{{ a.icon || accountType(a.type).icon }}</text></view>
        <view class="a-info">
          <view class="a-name-row"><text class="a-name">{{ a.name }}</text><text v-if="a.isDefault" class="badge">默认</text></view>
          <text class="a-type">{{ accountType(a.type).label }}</text>
        </view>
        <text :class="['a-balance mono', { neg: a.balance < 0 }]">{{ fixed(a.balance) }}</text>
      </view>

      <view v-if="loaded && !accounts.length" class="empty">
        <text class="empty-icon">💳</text>
        <text class="empty-text">还没有账户</text>
        <view class="btn btn-primary btn-sm" @click="edit()">添加账户</view>
      </view>
    </view>

    <text class="tip">账户余额需要手动维护，不会随账单自动增减</text>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { accountApi } from '@/api'
import { accountType } from './types'

const accounts = ref([])
const balance = ref({ totalAssets: 0, totalLiabilities: 0, netWorth: 0 })
const loaded = ref(false)

const fixed = (v) => Number(v || 0).toFixed(2)
const COLORS = { bank_card: '#7EB6FF', e_wallet: '#7DCEA0', credit_card: '#FF90B3', cash: '#FFD93D' }
const typeColor = (t) => COLORS[t] || '#E5E5E5'

onShow(async () => {
  const [list, total] = await Promise.all([accountApi.list(), accountApi.balance()])
  accounts.value = list
  balance.value = total
  loaded.value = true
})

const edit = (id) => uni.navigateTo({ url: `/pages/account/edit${id ? `?id=${id}` : ''}` })
</script>

<style lang="scss" scoped>
.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  background: $ln-accent;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
}
.summary {
  padding: 40rpx;
  margin: 32rpx 32rpx 8rpx;
  color: #fff;
  background: $ln-primary;
  @include brutal-box($ln-r-lg, $ln-bw-thick);
  @include brutal-shadow(10rpx);
}
.s-label {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
}
.s-net {
  display: block;
  margin: 12rpx 0 28rpx;
  font-size: 72rpx;
  font-weight: 900;
  letter-spacing: -2rpx;
}
.s-row {
  display: flex;
  align-items: center;
}
.s-col {
  flex: 1;
}
.s-sub {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
}
.s-val {
  display: block;
  margin-top: 6rpx;
  font-size: 38rpx;
  font-weight: 900;
}
.income-c {
  color: #4ade80;
}
.expense-c {
  color: #f87171;
}
.s-vdiv {
  width: $ln-bw-thin;
  height: 72rpx;
  margin: 0 32rpx;
  background: rgba(255, 255, 255, 0.3);
}
.list {
  padding: 32rpx 32rpx 0;
}
.account {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 24rpx;
  margin: 0 8rpx 28rpx 0;
  background: $ln-card;
  @include brutal-box($ln-r-lg);
  @include brutal-shadow(6rpx);
  @include brutal-press(6rpx);
}
.a-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 96rpx;
  height: 96rpx;
  font-size: 44rpx;
  @include brutal-box($ln-r-md, $ln-bw-thin);
}
.a-info {
  flex: 1;
  min-width: 0;
}
.a-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.a-name {
  font-size: 30rpx;
  font-weight: 800;
}
.badge {
  padding: 0 14rpx;
  font-size: 20rpx;
  font-family: inherit;
  background: $ln-primary-light;
}
.a-type {
  display: block;
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
.a-balance {
  font-size: 32rpx;
  font-weight: 800;
  &.neg {
    color: $ln-expense;
  }
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  padding: 100rpx 0;
}
.empty-icon {
  font-size: 96rpx;
}
.empty-text {
  font-size: 32rpx;
  font-weight: 800;
  color: $ln-text-secondary;
}
.tip {
  display: block;
  padding: 16rpx 32rpx 48rpx;
  text-align: center;
  font-size: 24rpx;
  color: $ln-text-secondary;
}
</style>
