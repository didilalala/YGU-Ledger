<template>
  <view class="bill-item" @click="$emit('click', bill)">
    <view class="left">
      <view class="icon" :style="{ background: categoryColor(bill.category?.name) }">
        <text>{{ bill.category?.icon || fallbackIcon(bill.type) }}</text>
      </view>
      <view class="info">
        <text class="title">{{ bill.description || bill.category?.name || '未分类' }}</text>
        <text class="meta mono">{{ shortDate(bill.date) }} · {{ bill.category?.name || '未分类' }}</text>
      </view>
    </view>
    <text :class="['badge', bill.type]">{{ bill.type === 'income' ? '+' : '-' }}¥{{ Number(bill.amount).toFixed(2) }}</text>
  </view>
</template>

<script setup>
import { categoryColor, fallbackIcon } from '@/utils/category-style'

defineProps({
  bill: { type: Object, required: true },
})
defineEmits(['click'])

const shortDate = (d) => `${Number(d.slice(5, 7))}月${Number(d.slice(8, 10))}日`
</script>

<style lang="scss" scoped>
/* 一行账单：彩色分类块 + 标题/元信息 + 圆润的金额徽章，对应原项目的 TransactionItem */
.bill-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  margin: 0 8rpx 32rpx 0;
  background: $ln-card;
  @include clay-box($ln-r-lg);
  @include clay-shadow(6rpx);
  @include clay-press(6rpx);
}
.left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}
.icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 96rpx;
  height: 96rpx;
  margin-right: 24rpx;
  font-size: 44rpx;
  @include clay-box($ln-r-md, $ln-bw-thin);
  text-shadow: 0 2rpx 0 rgba(255, 255, 255, 0.5);
}
.info {
  min-width: 0;
}
.title {
  display: block;
  margin-bottom: 6rpx;
  font-size: 30rpx;
  font-weight: 700;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.meta {
  display: block;
  font-size: 24rpx;
  font-weight: 500;
  color: $ln-text-secondary;
}
</style>
