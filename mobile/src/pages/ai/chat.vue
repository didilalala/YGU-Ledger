<template>
  <view class="page">
    <view class="toolbar muted">
      <text @click="newChat">＋ 新对话</text>
      <text @click="goSessions">历史会话 ›</text>
    </view>
    <scroll-view class="messages" scroll-y :scroll-into-view="scrollTarget">
      <view v-if="!messages.length" class="muted welcome">
        试试说：“中午吃饭花了 32 元，打车 18 元”
      </view>
      <view v-for="(m, i) in messages" :id="`msg-${i}`" :key="i" :class="['msg', m.role]">
        <view class="col">
          <text v-if="m.content || !m.bills?.length" class="bubble" user-select>{{ m.content || (m.pending ? '思考中…' : '') }}</text>
          <button v-if="m.needConfig" class="save" size="mini" @click="goConfig">去配置 AI 模型</button>
          <view v-if="m.bills?.length" class="bills">
            <bill-item v-for="(b, j) in m.bills" :key="j" :bill="toBillItem(b)" />
            <view v-if="m.bills.some((b) => !b.categoryId)" class="muted hint">
              部分账单没有匹配到分类，请在“账单”页手动补充
            </view>
            <button class="save" size="mini" :disabled="m.saving || !canSave(m)" @click="saveBills(m)">
              {{ saveLabel(m) }}
            </button>
          </view>
        </view>
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
import { onShow } from '@dcloudio/uni-app'
import { aiApi, billApi } from '@/api'
import { streamChat } from '@/api/stream'
import { STORAGE_KEYS, storage } from '@/utils/storage'
import BillItem from '@/components/bill-item/bill-item.vue'

const messages = ref([])
const input = ref('')
const sending = ref(false)
const sessionId = ref(null)
const scrollTarget = ref('')

function scrollToBottom() {
  nextTick(() => { scrollTarget.value = `msg-${messages.value.length - 1}` })
}

/** 后端 create_bills 返回的是平铺字段，转成 bill-item 需要的结构 */
const toBillItem = (b) => ({
  ...b,
  category: { name: b.categoryName, icon: b.categoryIcon },
})

// 没匹配到分类的账单无法保存（后端要求分类归属校验），其余可保存
const pendingBills = (m) => m.bills.filter((b) => !b.saved && b.categoryId)
const canSave = (m) => pendingBills(m).length > 0
const saveLabel = (m) => {
  if (m.saving) return '保存中…'
  const n = pendingBills(m).length
  return n ? `确认保存 ${n} 条` : '已保存'
}

/** 用户确认后才真正入库；AI 只负责识别，不直接写账 */
async function saveBills(m) {
  m.saving = true
  try {
    for (const b of pendingBills(m)) {
      await billApi.create({
        amount: b.amount, type: b.type, description: b.description,
        categoryId: b.categoryId, date: b.date, source: 'text',
      })
      b.saved = true // 逐条标记，中途失败时不会重复保存已成功的
    }
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (e) {
    // 请求层已弹出错误提示
  } finally {
    m.saving = false
  }
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
    case 'tool_result': {
      const { toolName, result } = evt.data
      if (toolName === 'create_bills' && result.success && result.data.bills.length) {
        reply.bills = result.data.bills.map((b) => ({ ...b, saved: false }))
        scrollToBottom()
      }
      break
    }
    case 'error':
      reply.content = evt.data.message || '出错了'
      if (reply.content.includes('请先配置')) reply.needConfig = true
      break
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  messages.value.push({ role: 'assistant', content: '', pending: true, bills: [], saving: false })
  // 取响应式代理：直接改原始对象不会触发视图更新
  const reply = messages.value[messages.value.length - 1]
  scrollToBottom()

  sending.value = true
  try {
    const { done } = streamChat({ message: text, sessionId: sessionId.value }, (evt) => handleEvent(evt, reply))
    await done
  } catch (e) {
    reply.content = e.message || '网络异常'
  } finally {
    reply.pending = false
    sending.value = false
  }
}

function newChat() {
  if (sending.value) return
  sessionId.value = null
  messages.value = []
}

/** 加载历史会话：只还原对话文字；工具调用过程和账单卡片不还原，避免重复保存 */
async function openSession(id) {
  const detail = await aiApi.session(id)
  sessionId.value = detail.id
  messages.value = detail.messages
    .filter((m) => (m.role === 'user' || m.role === 'assistant') && m.content)
    .map((m) => ({ role: m.role, content: m.content, bills: [] }))
  scrollToBottom()
}

onShow(() => {
  const id = storage.get(STORAGE_KEYS.OPEN_SESSION)
  if (id) {
    storage.remove(STORAGE_KEYS.OPEN_SESSION)
    openSession(id)
  }
})

const goConfig = () => uni.navigateTo({ url: '/pages/ai/config' })
const goSessions = () => uni.navigateTo({ url: '/pages/ai/sessions' })
</script>

<style lang="scss" scoped>
.page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--window-top) - var(--window-bottom));
}
.toolbar {
  display: flex;
  justify-content: space-between;
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
.col {
  max-width: 88%;
}
.bubble {
  display: inline-block;
  padding: 20rpx 28rpx;
  border-radius: 24rpx;
  background: $ln-card;
  white-space: pre-wrap;
  line-height: 1.6;
}
.bills {
  margin-top: 12rpx;
  padding: 0 24rpx 20rpx;
  background: $ln-card;
  border-radius: 24rpx;
}
.hint {
  padding-top: 12rpx;
  font-size: 24rpx;
}
.save {
  margin-top: 16rpx;
  background: $ln-primary;
  color: #fff;
  &[disabled] {
    background: $ln-border;
    color: $ln-text-secondary;
  }
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
