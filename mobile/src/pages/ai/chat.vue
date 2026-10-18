<template>
  <view class="page">
    <view class="toolbar muted" @click="goSessions">历史会话 ›</view>
    <scroll-view class="messages" scroll-y :scroll-into-view="scrollTarget">
      <view v-if="!messages.length" class="muted welcome">
        试试说：“中午吃饭花了 32 元，打车 18 元”
      </view>
      <view v-for="(m, i) in messages" :id="`msg-${i}`" :key="i" :class="['msg', m.role]">
        <text class="bubble" user-select>{{ m.content }}</text>
      </view>
    </scroll-view>

    <view class="composer">
      <!-- TODO: 语音按钮（uni.getRecorderManager → aiApi.transcribe）、拍照按钮（uni.chooseImage → base64） -->
      <input v-model="input" class="input" placeholder="描述你的消费或提问…" confirm-type="send" @confirm="send" />
      <button class="send" size="mini" :disabled="sending || !input.trim()" @click="send">发送</button>
    </view>
  </view>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { streamChat } from '@/api/stream'

const messages = ref([])
const input = ref('')
const sending = ref(false)
const sessionId = ref(null)
const scrollTarget = ref('')

function scrollToBottom() {
  nextTick(() => { scrollTarget.value = `msg-${messages.value.length - 1}` })
}

/** 处理后端推送的流式事件，事件类型见 backend/apps/ai/services/chat.py */
function handleEvent(evt, reply) {
  switch (evt.event) {
    case 'session_created':
      sessionId.value = evt.data.sessionId
      break
    case 'text_delta':
      reply.content += evt.data.content
      scrollToBottom()
      break
    case 'tool_result':
      // TODO: 以卡片形式展示 AI 创建/查询的账单
      break
    case 'error':
      reply.content = evt.data.message || '出错了'
      break
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  messages.value.push({ role: 'assistant', content: '' })
  const reply = messages.value[messages.value.length - 1]
  scrollToBottom()

  sending.value = true
  try {
    const { done } = streamChat({ message: text, sessionId: sessionId.value }, (evt) => handleEvent(evt, reply))
    await done
  } catch (e) {
    reply.content = e.message || '网络异常'
  } finally {
    sending.value = false
  }
}

// TODO: 在历史会话页选择后，带 sessionId 回到这里并加载会话消息
const goSessions = () => uni.navigateTo({ url: '/pages/ai/sessions' })
</script>

<style lang="scss" scoped>
.page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--window-top) - var(--window-bottom));
}
.toolbar {
  text-align: right;
  padding: 16rpx 32rpx 0;
}
.messages {
  flex: 1;
  height: 0;
  padding: 24rpx 32rpx;
  box-sizing: border-box;
}
.welcome {
  text-align: center;
  margin-top: 120rpx;
}
.msg {
  display: flex;
  margin-bottom: 24rpx;
  &.user {
    justify-content: flex-end;
    .bubble {
      background: $ln-primary;
      color: #fff;
    }
  }
}
.bubble {
  max-width: 80%;
  padding: 20rpx 28rpx;
  border-radius: 24rpx;
  background: $ln-card;
  white-space: pre-wrap;
  line-height: 1.6;
}
.composer {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  background: $ln-card;
  border-top: 1rpx solid $ln-border;
}
.input {
  flex: 1;
  height: 72rpx;
  padding: 0 24rpx;
  background: $ln-bg;
  border-radius: 36rpx;
}
.send {
  background: $ln-primary;
  color: #fff;
}
</style>
