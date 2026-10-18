<template>
  <view class="bill-item" @click="$emit('click', bill)">
    <view class="icon">{{ bill.category?.icon || (bill.type === 'income' ? '💰' : '📝') }}</view>
    <view class="info">
      <text class="title">{{ bill.description || bill.category?.name || '未分类' }}</text>
      <text class="muted">{{ bill.category?.name || '未分类' }} · {{ bill.date }}</text>
    </view>
    <text :class="['amount', bill.type]">{{ formatSignedMoney(bill.amount, bill.type) }}</text>
  </view>
</template>

<script setup>
import { formatSignedMoney } from '@/utils/format'

defineProps({
  bill: { type: Object, required: true },
})
defineEmits(['click'])
</script>

<style lang="scss" scoped>
.bill-item {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid $ln-border;
}
.icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: $ln-bg;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  margin-right: 24rpx;
}
.info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}
.title {
  font-size: 30rpx;
}
.amount {
  font-size: 32rpx;
  font-weight: 600;
}
</style>
