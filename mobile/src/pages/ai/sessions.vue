<template>
  <view class="card">
    <view v-for="s in sessions" :key="s.id" class="row">
      <text>{{ s.isPinned ? '📌 ' : '' }}{{ s.title || '新对话' }}</text>
      <text class="muted">{{ s.updatedAt.slice(0, 10) }}</text>
    </view>
    <view v-if="!sessions.length" class="muted empty">暂无历史会话</view>
    <!-- TODO: 点击进入会话、左滑置顶/删除（uni-swipe-action）、重命名 -->
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { aiApi } from '@/api'

const sessions = ref([])

onShow(async () => {
  sessions.value = (await aiApi.sessions({ page: 1, limit: 50 })).items
})
</script>

<style lang="scss" scoped>
.row {
  display: flex;
  justify-content: space-between;
  padding: 24rpx 0;
  border-bottom: 1rpx solid $ln-border;
}
.empty {
  text-align: center;
  padding: 48rpx 0;
}
</style>
