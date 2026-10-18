<template>
  <view class="page">
    <ln-navbar title="对话记录">
      <template #right><view class="new-btn" @click="newChat"><ln-icon name="plus" :size="32" color="#fff" :stroke="3" /><text>新对话</text></view></template>
    </ln-navbar>

    <view class="list">
      <view v-for="s in sessions" :key="s.id" class="session" @click="open(s)" @longpress="more(s)">
        <view class="s-icon"><text>{{ s.isPinned ? '📌' : '💬' }}</text></view>
        <view class="s-info">
          <text class="s-title">{{ s.title || '新对话' }}</text>
          <text class="s-meta mono">{{ s.updatedAt.slice(0, 10) }}</text>
        </view>
        <ln-icon name="chevron-right" :size="36" color="#737373" />
      </view>

      <view v-if="loaded && !sessions.length" class="empty">
        <text class="empty-icon">💬</text>
        <text class="empty-text">暂无历史会话</text>
      </view>
    </view>

    <text v-if="sessions.length" class="tip">长按会话可置顶或删除</text>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { aiApi } from '@/api'
import { STORAGE_KEYS, storage } from '@/utils/storage'

const sessions = ref([])
const loaded = ref(false)

const load = async () => {
  sessions.value = (await aiApi.sessions({ page: 1, limit: 50 })).items
  loaded.value = true
}
onShow(load)

// 聊天页是 tabBar 页面，switchTab 不能带参数，通过本地存储传递要打开的会话
function open(s) {
  storage.set(STORAGE_KEYS.OPEN_SESSION, s.id)
  uni.switchTab({ url: '/pages/ai/chat' })
}
const newChat = () => uni.switchTab({ url: '/pages/ai/chat' })

function more(s) {
  uni.showActionSheet({
    itemList: [s.isPinned ? '取消置顶' : '置顶', '删除'],
    success: async ({ tapIndex }) => {
      if (tapIndex === 0) {
        await aiApi.togglePin(s.id)
      } else {
        const { confirm } = await uni.showModal({ title: '删除会话', content: '删除后无法恢复，确定吗？' })
        if (!confirm) return
        await aiApi.removeSession(s.id)
      }
      load()
    },
  })
}
</script>

<style lang="scss" scoped>
.new-btn {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 10rpx 24rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: #fff;
  background: $ln-primary;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
}
.list {
  padding: 32rpx;
}
.session {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  background: $ln-card;
  @include brutal-box($ln-r-lg, $ln-bw-thin);
  &:active {
    background: $ln-bg;
  }
}
.s-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 80rpx;
  height: 80rpx;
  font-size: 38rpx;
  background: $ln-accent;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
}
.s-info {
  flex: 1;
  min-width: 0;
}
.s-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.s-meta {
  display: block;
  margin-top: 4rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  padding-top: 200rpx;
}
.empty-icon {
  font-size: 96rpx;
}
.empty-text {
  font-size: 30rpx;
  font-weight: 700;
  color: $ln-text-secondary;
}
.tip {
  display: block;
  padding-bottom: 48rpx;
  text-align: center;
  font-size: 24rpx;
  color: $ln-text-secondary;
}
</style>
