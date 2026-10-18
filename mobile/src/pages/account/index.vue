<template>
  <view>
    <view class="card summary">
      <text class="muted">净资产</text>
      <text class="net">{{ formatMoney(balance.netWorth) }}</text>
      <view class="row">
        <view class="col"><text class="muted">总资产</text><text class="income">{{ formatMoney(balance.totalAssets) }}</text></view>
        <view class="col"><text class="muted">总负债</text><text class="expense">{{ formatMoney(balance.totalLiabilities) }}</text></view>
      </view>
    </view>

    <view v-for="a in accounts" :key="a.id" class="card account" @click="edit(a.id)">
      <text class="icon">{{ a.icon || accountType(a.type).icon }}</text>
      <view class="info">
        <view class="name-row">
          <text class="name">{{ a.name }}</text>
          <text v-if="a.isDefault" class="tag">默认</text>
        </view>
        <text class="muted">{{ accountType(a.type).label }}</text>
      </view>
      <text :class="{ expense: a.balance < 0 }">{{ formatMoney(a.balance) }}</text>
    </view>
    <view v-if="loaded && !accounts.length" class="card muted empty">还没有账户</view>

    <view class="muted tip">账户余额需要手动维护，不会随账单自动增减</view>
    <view class="form-actions">
      <button class="primary" @click="edit()">添加账户</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { accountApi } from '@/api'
import { formatMoney } from '@/utils/format'
import { accountType } from './types'

const accounts = ref([])
const balance = ref({ totalAssets: 0, totalLiabilities: 0, netWorth: 0 })
const loaded = ref(false)

onShow(async () => {
  const [list, total] = await Promise.all([accountApi.list(), accountApi.balance()])
  accounts.value = list
  balance.value = total
  loaded.value = true
})

const edit = (id) => uni.navigateTo({ url: `/pages/account/edit${id ? `?id=${id}` : ''}` })
</script>

<style lang="scss" scoped>
.summary {
  background: $ln-primary;
  color: #fff;
  .muted,
  .income,
  .expense {
    color: rgba(255, 255, 255, 0.85);
  }
}
.net {
  display: block;
  font-size: 56rpx;
  font-weight: 700;
  margin: 8rpx 0 16rpx;
}
.row {
  display: flex;
}
.col {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.account {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.icon {
  font-size: 48rpx;
}
.info {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.name {
  font-weight: 600;
}
.tag {
  padding: 2rpx 12rpx;
  font-size: 22rpx;
  border-radius: 8rpx;
  color: $ln-primary;
  background: rgba(79, 110, 247, 0.12);
}
.empty,
.tip {
  text-align: center;
}
</style>
