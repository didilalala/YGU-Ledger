<template>
  <view class="page">
    <ln-navbar title="账单详情" />

    <view v-if="bill" class="content">
      <view class="amount-section">
        <view class="icon-block" :style="{ background: categoryColor(bill.category?.name) }">
          <text>{{ bill.category?.icon || fallbackIcon(bill.type) }}</text>
        </view>
        <text :class="['type-badge', bill.type]">{{ bill.type === 'income' ? '收入' : '支出' }}</text>
        <text :class="['amount mono', bill.type]">¥ {{ Number(bill.amount).toFixed(2) }}</text>
        <text class="cat-label">{{ bill.category?.name || '未分类' }}</text>
      </view>

      <view class="detail-card">
        <view class="row">
          <text class="label">分类</text>
          <text class="value">{{ bill.category?.icon }} {{ bill.category?.name || '未分类' }}</text>
        </view>
        <view class="divider" />
        <view class="row">
          <text class="label">日期</text>
          <text class="value mono">{{ bill.date }}</text>
        </view>
        <view class="divider" />
        <view class="row">
          <text class="label">备注</text>
          <text class="value">{{ bill.description || '-' }}</text>
        </view>
        <view class="divider" />
        <view class="row">
          <text class="label">来源</text>
          <text class="value">{{ SOURCE_LABELS[bill.source] || bill.source }}</text>
        </view>
        <template v-if="bill.tags?.length">
          <view class="divider" />
          <view class="row">
            <text class="label">标签</text>
            <view class="tags"><text v-for="t in bill.tags" :key="t" class="tag">{{ t }}</text></view>
          </view>
        </template>
      </view>
    </view>

    <view class="bottom-actions">
      <view class="btn btn-primary" @click="edit">编辑</view>
      <view class="btn del" @click="remove">删除</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { billApi } from '@/api'
import { categoryColor, fallbackIcon } from '@/utils/category-style'

const SOURCE_LABELS = { manual: '手动', voice: '语音', ocr: '拍照', text: 'AI 对话', notification: '支付通知' }

const bill = ref(null)
let billId

const load = async () => { bill.value = await billApi.detail(billId) }

onLoad((query) => { billId = query.id })
// 编辑页返回后要刷新；onShow 在 onLoad 之后也会触发，所以首次加载也在这里
onShow(() => load().catch(() => {}))

const edit = () => uni.navigateTo({ url: `/pages/bills/create?id=${billId}` })

function remove() {
  uni.showModal({
    title: '删除账单',
    content: '删除后无法恢复，确定删除吗？',
    success: async ({ confirm }) => {
      if (!confirm) return
      await billApi.remove(billId)
      uni.showToast({ title: '已删除', icon: 'success' })
      setTimeout(() => uni.navigateBack(), 500)
    },
  })
}
</script>

<style lang="scss" scoped>
.page {
  padding-bottom: calc(180rpx + env(safe-area-inset-bottom));
}
.content {
  padding: 32rpx;
}
.amount-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48rpx;
  margin-bottom: 32rpx;
  background: $ln-card;
  @include brutal-box($ln-r-lg, $ln-bw-thin);
}
.icon-block {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 128rpx;
  height: 128rpx;
  margin-bottom: 24rpx;
  font-size: 64rpx;
  @include brutal-box($ln-r-md);
}
.type-badge {
  padding: 4rpx 24rpx;
  margin-bottom: 16rpx;
  font-size: 26rpx;
  font-weight: 800;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
  &.expense {
    color: $ln-expense;
    background: $ln-expense-bg;
  }
  &.income {
    color: $ln-income;
    background: $ln-income-bg;
  }
}
.amount {
  margin-bottom: 16rpx;
  font-size: 80rpx;
  font-weight: 800;
  letter-spacing: -2rpx;
  &.expense {
    color: $ln-expense;
  }
  &.income {
    color: $ln-income;
  }
}
.cat-label {
  font-size: 28rpx;
  font-weight: 700;
  color: $ln-text-secondary;
}
.detail-card {
  overflow: hidden;
  margin-right: 6rpx;
  background: $ln-card;
  @include brutal-box($ln-r-lg);
  @include brutal-shadow(6rpx);
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32rpx;
  padding: 32rpx;
}
.label {
  flex-shrink: 0;
  font-size: 28rpx;
  font-weight: 700;
  color: $ln-text-secondary;
}
.value {
  font-size: 28rpx;
  font-weight: 700;
  text-align: right;
}
.divider {
  height: $ln-bw-thin;
  margin: 0 32rpx;
  background: $ln-stroke;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12rpx;
}
.tag {
  padding: 4rpx 16rpx;
  font-size: 24rpx;
  font-weight: 700;
  background: $ln-accent;
  @include brutal-box(12rpx, 3rpx);
}
.bottom-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  display: flex;
  gap: 24rpx;
  padding: 24rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
  background: $ln-card;
  border-top: $ln-bw-thin solid $ln-stroke;
  .btn {
    flex: 1;
  }
  .del {
    color: $ln-error;
    background: rgba(239, 68, 68, 0.08);
    border-color: $ln-error;
    box-shadow: none;
  }
}
</style>
