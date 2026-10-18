<template>
  <view class="card">
    <view v-for="s in sessions" :key="s.id" class="row" @click="open(s)" @longpress="more(s)">
      <text class="title">{{ s.isPinned ? '📌 ' : '' }}{{ s.title || '新对话' }}</text>
      <text class="muted">{{ s.updatedAt.slice(0, 10) }}</text>
    </view>
    <view v-if="!sessions.length" class="muted empty">暂无历史会话</view>
    <view v-if="sessions.length" class="muted tip">长按会话可置顶或删除</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { aiApi } from '@/api'
import { STORAGE_KEYS, storage } from '@/utils/storage'

const sessions = ref([])

const load = async () => {
  sessions.value = (await aiApi.sessions({ page: 1, limit: 50 })).items
}
onShow(load)

// 聊天页是 tabBar 页面，switchTab 不能带参数，通过本地存储传递要打开的会话
function open(s) {
  storage.set(STORAGE_KEYS.OPEN_SESSION, s.id)
  uni.switchTab({ url: '/pages/ai/chat' })
}

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
.row {
  display: flex;
  justify-content: space-between;
  padding: 24rpx 0;
  border-bottom: 1rpx solid $ln-border;
}
.title {
  flex: 1;
  margin-right: 24rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty,
.tip {
  text-align: center;
  padding: 32rpx 0 0;
}
</style>
