<template>
  <view v-if="bill">
    <view class="card head">
      <text class="icon">{{ bill.category?.icon || '📝' }}</text>
      <text class="muted">{{ bill.category?.name || '未分类' }}</text>
      <text :class="['amount', bill.type]">{{ formatSignedMoney(bill.amount, bill.type) }}</text>
    </view>

    <view class="card">
      <view class="row"><text class="muted">日期</text><text>{{ bill.date }}</text></view>
      <view class="row"><text class="muted">备注</text><text>{{ bill.description || '-' }}</text></view>
      <view class="row"><text class="muted">来源</text><text>{{ SOURCE_LABELS[bill.source] || bill.source }}</text></view>
      <view v-if="bill.tags?.length" class="row"><text class="muted">标签</text><text>{{ bill.tags.join('、') }}</text></view>
    </view>

    <!-- TODO: 编辑账单（复用 create 页面，传入 id 进入编辑模式） -->
    <view class="actions">
      <button type="warn" @click="remove">删除</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { billApi } from '@/api'
import { formatSignedMoney } from '@/utils/format'

const SOURCE_LABELS = { manual: '手动', voice: '语音', ocr: '拍照', text: 'AI 对话', notification: '支付通知' }

const bill = ref(null)
let billId

onLoad(async (query) => {
  billId = query.id
  bill.value = await billApi.detail(billId)
})

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
.head {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}
.icon {
  font-size: 72rpx;
}
.amount {
  font-size: 56rpx;
  font-weight: 700;
}
.row {
  display: flex;
  justify-content: space-between;
  padding: 16rpx 0;
}
.actions {
  padding: 32rpx;
}
</style>
