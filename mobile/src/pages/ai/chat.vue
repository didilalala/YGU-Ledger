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
          <view v-if="m.images?.length" class="thumbs">
            <image v-for="(src, k) in m.images" :key="k" class="thumb" :src="src" mode="aspectFill"
              @click="preview(m.images, k)" />
          </view>
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

    <view v-if="pendingImages.length" class="pending">
      <view v-for="(src, k) in pendingImages" :key="k" class="pending-item">
        <image class="thumb" :src="src" mode="aspectFill" />
        <text class="remove" @click="pendingImages.splice(k, 1)">×</text>
      </view>
    </view>

    <view class="composer">
      <text class="icon-btn" @click="toggleVoiceMode">{{ voiceMode ? '⌨️' : '🎤' }}</text>
      <view v-if="voiceMode" :class="['hold', { active: voice.state !== 'idle', cancel: voice.willCancel }]"
        @touchstart.prevent="onHoldStart" @touchmove.prevent="onHoldMove" @touchend.prevent="onHoldEnd"
        @touchcancel.prevent="onHoldCancel">
        <text>{{ holdLabel }}</text>
      </view>
      <input v-else v-model="input" class="input" placeholder="描述你的消费或提问…" confirm-type="send" @confirm="send" />
      <text v-if="pendingImages.length < MAX_IMAGES" class="icon-btn" @click="chooseImage">📷</text>
      <button v-if="!voiceMode" class="send" size="mini" :disabled="!canSend" @click="send">发送</button>
    </view>
  </view>
</template>

<script setup>
import { computed, nextTick, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { aiApi, billApi } from '@/api'
import { streamChat } from '@/api/stream'
import { STORAGE_KEYS, storage } from '@/utils/storage'
import { pickImages } from '@/utils/media'
import { createRecorder } from '@/utils/recorder'
import BillItem from '@/components/bill-item/bill-item.vue'

const messages = ref([])
const input = ref('')
const sending = ref(false)
const sessionId = ref(null)
const scrollTarget = ref('')
const pendingImages = ref([])
const MAX_IMAGES = 3 // 每条消息最多 3 张，控制请求体和模型用量
const canSend = computed(() => !sending.value && (input.value.trim() || pendingImages.value.length))

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

/** 发送一条消息；语音识别完成后也走这里 */
async function sendMessage(text, images = []) {
  if ((!text && !images.length) || sending.value) return
  messages.value.push({ role: 'user', content: text, images })
  messages.value.push({ role: 'assistant', content: '', pending: true, bills: [], saving: false })
  // 取响应式代理：直接改原始对象不会触发视图更新
  const reply = messages.value[messages.value.length - 1]
  scrollToBottom()

  sending.value = true
  try {
    const { done } = streamChat(
      { message: text, sessionId: sessionId.value, ...(images.length ? { images } : {}) },
      (evt) => handleEvent(evt, reply),
    )
    await done
  } catch (e) {
    reply.content = e.message || '网络异常'
  } finally {
    reply.pending = false
    sending.value = false
  }
}

function send() {
  if (!canSend.value) return
  const text = input.value.trim()
  const images = pendingImages.value
  input.value = ''
  pendingImages.value = []
  sendMessage(text, images)
}

// ---------- 拍照 / 相册 ----------

function chooseImage() {
  uni.showActionSheet({
    itemList: ['拍照', '从相册选择'],
    success: async ({ tapIndex }) => {
      try {
        const picked = await pickImages(tapIndex === 0 ? 'camera' : 'album', MAX_IMAGES - pendingImages.value.length)
        pendingImages.value.push(...picked.slice(0, MAX_IMAGES - pendingImages.value.length))
      } catch (e) {
        uni.showToast({ title: '无法读取图片', icon: 'none' })
      }
    },
  })
}

const preview = (urls, current) => uni.previewImage({ urls, current })

// ---------- 语音：按住说话，松手识别并发送，上滑取消 ----------

const CANCEL_DISTANCE = 80 // 手指上滑超过这个距离（px）视为取消
const voiceMode = ref(false)
const voice = reactive({ state: 'idle', willCancel: false }) // idle | recording | transcribing
let recorder = null
let startY = 0

const holdLabel = computed(() => {
  if (voice.state === 'transcribing') return '识别中…'
  if (voice.state === 'recording') return voice.willCancel ? '松开取消' : '松开发送，上滑取消'
  return '按住 说话'
})

const toggleVoiceMode = () => { if (voice.state === 'idle') voiceMode.value = !voiceMode.value }

async function onHoldStart(e) {
  if (voice.state !== 'idle' || sending.value) return
  startY = e.touches[0].clientY
  voice.state = 'recording'
  voice.willCancel = false
  recorder = createRecorder()
  try {
    await recorder.start()
  } catch (err) {
    voice.state = 'idle'
    recorder = null
    uni.showToast({ title: err.message || '无法开始录音，请检查麦克风权限', icon: 'none' })
  }
}

function onHoldMove(e) {
  if (voice.state !== 'recording') return
  voice.willCancel = startY - e.touches[0].clientY > CANCEL_DISTANCE
}

async function onHoldEnd() {
  if (voice.state !== 'recording' || !recorder) return
  const current = recorder
  recorder = null
  if (voice.willCancel) {
    current.cancel()
    return resetVoice()
  }
  voice.state = 'transcribing'
  try {
    const clip = await current.stop()
    if (!clip) return uni.showToast({ title: '说话时间太短', icon: 'none' })
    const { text } = await aiApi.transcribe(clip.base64, clip.mimeType)
    if (!text) return uni.showToast({ title: '没听清，请再说一次', icon: 'none' })
    resetVoice()
    await sendMessage(text, [])
  } catch (err) {
    uni.showToast({ title: err.message || '语音识别失败', icon: 'none' })
  } finally {
    resetVoice()
  }
}

function onHoldCancel() {
  recorder?.cancel()
  recorder = null
  resetVoice()
}

function resetVoice() {
  voice.state = 'idle'
  voice.willCancel = false
}

function newChat() {
  if (sending.value) return
  sessionId.value = null
  messages.value = []
}

/** 后端把图片列表存成 JSON 字符串 */
function parseImages(raw) {
  if (!raw) return []
  try {
    const list = JSON.parse(raw)
    return Array.isArray(list) ? list : []
  } catch (e) {
    return []
  }
}

/** 加载历史会话：只还原对话文字；工具调用过程和账单卡片不还原，避免重复保存 */
async function openSession(id) {
  const detail = await aiApi.session(id)
  sessionId.value = detail.id
  messages.value = detail.messages
    .filter((m) => (m.role === 'user' || m.role === 'assistant') && (m.content || m.imageUrl))
    .map((m) => ({ role: m.role, content: m.content, bills: [], images: parseImages(m.imageUrl) }))
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
.thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  justify-content: flex-end;
  margin-bottom: 8rpx;
}
.thumb {
  width: 160rpx;
  height: 160rpx;
  border-radius: 12rpx;
}
.pending {
  display: flex;
  gap: 16rpx;
  padding: 12rpx 24rpx 0;
  background: $ln-card;
}
.pending-item {
  position: relative;
}
.remove {
  position: absolute;
  top: -10rpx;
  right: -10rpx;
  width: 40rpx;
  height: 40rpx;
  line-height: 38rpx;
  text-align: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
}
.icon-btn {
  font-size: 44rpx;
  padding: 0 8rpx;
}
.hold {
  flex: 1;
  height: 72rpx;
  line-height: 72rpx;
  text-align: center;
  border-radius: 36rpx;
  background: $ln-bg;
  user-select: none;
  &.active {
    background: $ln-primary;
    color: #fff;
  }
  &.cancel {
    background: $ln-expense;
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
