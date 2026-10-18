<template>
  <view class="page">
    <ln-navbar title="AI 助手" :back="false">
      <template #left><view class="nav-icon" @click="goSessions"><ln-icon name="menu" :size="44" /></view></template>
      <template #right><view class="nav-icon" @click="newChat"><ln-icon name="square-pen" :size="44" color="#3B82F6" /></view></template>
    </ln-navbar>

    <scroll-view class="messages" scroll-y :scroll-into-view="scrollTarget" scroll-with-animation>
      <view v-if="!messages.length" class="welcome">
        <view class="welcome-bubble"><text>试试说：“中午吃饭花了 32 元，打车 18 元”</text></view>
      </view>

      <view v-for="(m, i) in messages" :id="`msg-${i}`" :key="i" :class="['row', m.role]">
        <!-- 用户 -->
        <view v-if="m.role === 'user'" class="user-col">
          <view v-if="m.images?.length" class="thumbs">
            <image v-for="(src, k) in m.images" :key="k" class="thumb" :src="src" mode="aspectFill" @click="preview(m.images, k)" />
          </view>
          <view v-if="m.content" class="bubble user-bubble"><text user-select>{{ m.content }}</text></view>
        </view>

        <!-- AI -->
        <template v-else>
          <image v-if="avatar" class="avatar" :src="avatar" mode="aspectFit" />
          <view v-else class="avatar fallback"><text>🤖</text></view>

          <view class="ai-col">
            <!-- 思考过程（有推理内容的模型） -->
            <view v-if="m.thinking" class="bubble ai-bubble think" @click="m.showThinking = !m.showThinking">
              <view class="think-head">
                <text class="think-title">{{ m.pending && !m.content ? '思考中…' : thinkingText(m.thinkingMs) }}</text>
                <ln-icon name="chevron-down" :size="30" color="#737373" />
              </view>
              <text v-if="m.showThinking" class="think-body">{{ m.thinking }}</text>
            </view>

            <view v-if="m.content || (m.pending && !m.thinking && !m.cards.length && !m.bills.length)"
              :class="['bubble', 'ai-bubble', { error: m.failed }]">
              <text user-select>{{ m.content || '思考中…' }}</text>
            </view>
            <view v-if="m.needConfig" class="btn btn-primary btn-sm cfg-btn" @click="goConfig">去配置 AI 模型</view>

            <!-- 统计 / 查询等工具结果 -->
            <view v-for="(c, k) in m.cards" :key="k" class="bubble ai-bubble card-bubble">
              <text class="card-title">{{ c.title }}</text>
              <view v-if="c.kind === 'stats'" class="stats-box">
                <view v-for="r in c.rows" :key="r.label" class="stats-row">
                  <text class="stats-label">{{ r.label }}</text>
                  <text :class="['stats-value mono', r.tone]">{{ r.value }}</text>
                </view>
              </view>
              <view v-if="c.kind === 'list'" class="list-box">
                <view v-for="it in c.items" :key="it.id" class="list-row">
                  <text class="l-date mono">{{ it.date }}</text>
                  <text class="l-desc">{{ it.description }}</text>
                  <text :class="['l-amount mono', it.type]">{{ it.amount }}</text>
                </view>
              </view>
            </view>

            <!-- 识别出的账单：确认后才保存 -->
            <view v-for="(b, k) in m.bills" :key="k" class="bill-wrap">
              <view class="bill-card" :style="{ background: BILL_TONES[b.type].bg, borderColor: BILL_TONES[b.type].border }">
                <text class="bill-date">{{ b.date }}</text>
                <view class="bill-main">
                  <view class="bill-icon" :style="{ background: BILL_TONES[b.type].iconBg }"><text>{{ b.categoryIcon || (b.type === 'expense' ? '💰' : '💵') }}</text></view>
                  <view class="bill-info">
                    <text class="bill-cat">{{ b.categoryName }}{{ b.categoryId ? '' : '（未匹配分类）' }}</text>
                    <text class="bill-desc">{{ b.description }}</text>
                  </view>
                  <text class="bill-amount" :style="{ color: BILL_TONES[b.type].amount }">{{ billAmountText(b) }}</text>
                </view>
              </view>
              <view v-if="!b.saved" class="bill-actions">
                <view class="mini-btn edit" @click="editBill(m, b)"><ln-icon name="pencil" :size="28" color="#3B82F6" /><text>修改</text></view>
                <view class="mini-btn del" @click="removeBill(m, b)"><ln-icon name="trash" :size="28" color="#EF4444" /><text>删除</text></view>
              </view>
              <view v-else class="saved-tag"><ln-icon name="check" :size="28" color="#16A34A" :stroke="3" /><text>已保存</text></view>
            </view>
          </view>
        </template>
      </view>
      <view class="bottom-space" />
    </scroll-view>

    <!-- 待保存的账单 -->
    <view v-if="pending.length" class="pending-bar">
      <text class="pending-text">{{ pending.length }} 条账单待保存</text>
      <view class="save-all" @click="saveAll"><ln-icon name="check" :size="30" color="#fff" :stroke="3" /><text>{{ savingAll ? '保存中…' : '全部保存' }}</text></view>
    </view>

    <!-- 待发送的图片 -->
    <view v-if="pendingImages.length" class="pending-images">
      <view v-for="(src, k) in pendingImages" :key="k" class="pi-item">
        <image class="pi-thumb" :src="src" mode="aspectFill" />
        <view class="pi-remove" @click="pendingImages.splice(k, 1)"><ln-icon name="x" :size="22" color="#fff" :stroke="3" /></view>
      </view>
    </view>

    <view class="composer">
      <view v-if="pendingImages.length < MAX_IMAGES" class="media-btn" @click="chooseImage"><ln-icon name="camera" :size="44" color="#3B82F6" /></view>
      <view v-if="voiceMode" :class="['hold', { active: voice.state !== 'idle', cancel: voice.willCancel }]" @touchstart.prevent="onHoldStart"
        @touchmove.prevent="onHoldMove" @touchend.prevent="onHoldEnd" @touchcancel.prevent="onHoldCancel">
        <text>{{ holdLabel }}</text>
      </view>
      <view v-else class="input-wrap">
        <input v-model="input" class="input" placeholder="点击输入文字" placeholder-class="ph" confirm-type="send" @confirm="send" />
      </view>
      <view v-if="hasInput && !voiceMode" :class="['send-btn', { off: !canSend }]" @click="send"><ln-icon name="send" :size="40" color="#fff" /></view>
      <view v-else class="media-btn" @click="toggleVoiceMode"><ln-icon :name="voiceMode ? 'keyboard' : 'mic'" :size="44" color="#3B82F6" /></view>
    </view>

    <bill-edit-sheet :visible="editing.visible" :bill="editing.bill" :categories="categoryStore.list" @close="editing.visible = false" @save="onEdited" />
    <ln-tabbar current="chat" />
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
import { useCategoryStore } from '@/stores/category'
import { BILL_TONES, billAmountText, canSaveBill, describeToolResult, pendingBills as collectPending, thinkingText } from '@/utils/chat'
import { providerLogo } from './providers'

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

const categoryStore = useCategoryStore()
const avatar = ref('') // 默认模型服务商的图标，作为 AI 头像

async function loadAvatar() {
  try {
    const configs = await aiApi.configs()
    const current = configs.find((c) => c.isDefault) || configs[0]
    avatar.value = current ? providerLogo(current.provider) : ''
  } catch (e) { /* 头像拿不到就用默认图标 */ }
}

// ---------- 账单卡片：AI 只负责识别，用户确认后才入库 ----------

const pending = computed(() => collectPending(messages.value))
const savingAll = ref(false)

async function saveOne(bill) {
  await billApi.create({
    amount: bill.amount, type: bill.type, description: bill.description,
    categoryId: bill.categoryId, date: bill.date, source: 'text',
  })
  bill.saved = true // 逐条标记，中途失败时不会重复保存已成功的
}

async function saveBill(bill) {
  if (!canSaveBill(bill)) return
  try {
    await saveOne(bill)
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (e) { /* 请求层已提示 */ }
}

async function saveAll() {
  if (savingAll.value) return
  savingAll.value = true
  try {
    for (const bill of pending.value) await saveOne(bill)
    uni.showToast({ title: '已全部保存', icon: 'success' })
  } catch (e) { /* 请求层已提示 */ } finally {
    savingAll.value = false
  }
}

function removeBill(message, bill) {
  message.bills = message.bills.filter((b) => b !== bill)
}

const editing = reactive({ visible: false, bill: null, message: null })
function editBill(message, bill) {
  Object.assign(editing, { visible: true, bill, message })
}
function onEdited(updated) {
  const list = editing.message.bills
  list.splice(list.indexOf(editing.bill), 1, updated)
  editing.visible = false
}

/** 处理后端推送的流式事件，事件类型见 backend/apps/ai/services/chat.py */
function handleEvent(evt, reply) {
  switch (evt.event) {
    case 'session_created':
      sessionId.value = evt.data.sessionId
      break
    case 'thinking_delta':
      reply.thinking += evt.data.content
      break
    case 'text_delta':
      reply.content += evt.data.content
      scrollToBottom()
      break
    case 'tool_result': {
      const card = describeToolResult(evt.data.toolName, evt.data.result)
      if (card.kind === 'bills') reply.bills.push(...card.bills)
      else reply.cards.push(card)
      scrollToBottom()
      break
    }
    case 'done':
      reply.thinkingMs = evt.data.thinkingTimeMs
      break
    case 'error':
      reply.content = evt.data.message || '出错了'
      reply.failed = true
      if (reply.content.includes('请先配置')) reply.needConfig = true
      break
  }
}

/** 发送一条消息；语音识别完成后也走这里 */
async function sendMessage(text, images = []) {
  if ((!text && !images.length) || sending.value) return
  messages.value.push({ role: 'user', content: text, images })
  messages.value.push({ role: 'assistant', content: '', pending: true, bills: [], cards: [], thinking: '', thinkingMs: null, showThinking: false })
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
    .map((m) => ({ role: m.role, content: m.content, bills: [], cards: [], thinking: '', images: parseImages(m.imageUrl) }))
  scrollToBottom()
}

onShow(() => {
  categoryStore.load().catch(() => {})
  loadAvatar()
  const id = storage.get(STORAGE_KEYS.OPEN_SESSION)
  if (id) {
    storage.remove(STORAGE_KEYS.OPEN_SESSION)
    openSession(id)
  }
})

const goConfig = () => uni.navigateTo({ url: '/pages/ai/config' })
const goSessions = () => uni.navigateTo({ url: '/pages/ai/sessions' })
const hasInput = computed(() => !!input.value.trim() || pendingImages.value.length > 0)
</script>

<style lang="scss" scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-bottom: calc(144rpx + env(safe-area-inset-bottom));
}
.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
}
.messages {
  flex: 1;
  height: 0;
  padding: 32rpx;
}
.welcome {
  display: flex;
  justify-content: center;
  margin-top: 120rpx;
}
.welcome-bubble {
  padding: 24rpx 32rpx;
  font-weight: 600;
  color: $ln-text-secondary;
  background: $ln-card;
  @include brutal-box($ln-r-lg, $ln-bw-thin);
}
.row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 28rpx;
  &.user {
    justify-content: flex-end;
  }
}
.user-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  max-width: 84%;
}
.ai-col {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16rpx;
  min-width: 0;
  max-width: 84%;
}
.avatar {
  flex-shrink: 0;
  width: 56rpx;
  height: 56rpx;
  margin: 8rpx 16rpx 0 0;
  &.fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40rpx;
  }
}
.bubble {
  padding: 24rpx 28rpx;
  font-size: 30rpx;
  font-weight: 600;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  @include brutal-box($ln-r-lg, $ln-bw-thin);
}
.user-bubble {
  color: #fff;
  background: $ln-primary;
  border-bottom-right-radius: 8rpx;
}
.ai-bubble {
  background: $ln-card;
  border-bottom-left-radius: 8rpx;
  &.error {
    color: #d32f2f;
    background: #ffebee;
  }
}
.thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  justify-content: flex-end;
  margin-bottom: 12rpx;
}
.thumb {
  width: 200rpx;
  height: 200rpx;
  border: $ln-bw-thin solid $ln-stroke;
  border-radius: $ln-r-sm;
}
.think {
  font-size: 26rpx;
  color: $ln-text-secondary;
}
.think-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}
.think-body {
  display: block;
  margin-top: 16rpx;
  font-weight: 500;
  line-height: 1.7;
}
.cfg-btn {
  align-self: flex-start;
}
.card-bubble {
  min-width: 420rpx;
}
.card-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 30rpx;
  font-weight: 800;
}
.stats-box {
  padding: 8rpx 24rpx;
  background: #f5f5f5;
  border-radius: $ln-r-md;
}
.stats-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 0;
  border-bottom: 2rpx solid #e0e0e0;
  &:last-child {
    border-bottom: none;
  }
}
.stats-label {
  font-size: 28rpx;
  color: $ln-text-secondary;
}
.stats-value {
  font-size: 32rpx;
  font-weight: 800;
  &.expense {
    color: $ln-expense;
  }
  &.income {
    color: $ln-income;
  }
}
.list-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 12rpx 0;
  border-bottom: 2rpx solid #e0e0e0;
  font-size: 26rpx;
  font-weight: 500;
}
.l-date {
  width: 180rpx;
  color: $ln-text-secondary;
}
.l-desc {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.l-amount {
  font-weight: 800;
  &.expense {
    color: $ln-expense;
  }
  &.income {
    color: $ln-income;
  }
}

/* 账单预览卡 */
.bill-wrap {
  width: 100%;
  min-width: 560rpx;
}
.bill-card {
  padding: 24rpx;
  border: 2rpx solid;
  border-radius: $ln-r-md;
  box-shadow: 4rpx 4rpx 0 rgba(0, 0, 0, 0.12);
}
.bill-date {
  display: block;
  margin-bottom: 16rpx;
  font-size: 24rpx;
  color: #666;
}
.bill-main {
  display: flex;
  align-items: center;
}
.bill-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 88rpx;
  height: 88rpx;
  margin-right: 24rpx;
  font-size: 42rpx;
  border-radius: 50%;
}
.bill-info {
  flex: 1;
  min-width: 0;
}
.bill-cat {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
}
.bill-desc {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: #666;
}
.bill-amount {
  font-size: 36rpx;
  font-weight: 800;
}
.bill-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 16rpx;
}
.mini-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 24rpx;
  font-size: 26rpx;
  font-weight: 600;
  background: #fff;
  border: 2rpx solid;
  border-radius: $ln-r-sm;
  &.edit {
    color: $ln-primary;
    border-color: $ln-primary;
  }
  &.del {
    color: $ln-error;
    border-color: $ln-error;
  }
}
.saved-tag {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 16rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: $ln-income;
}
.bottom-space {
  height: 16rpx;
}

/* 待保存条 */
.pending-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 32rpx;
  background: rgba(59, 130, 246, 0.1);
  border-top: $ln-bw-thin solid $ln-stroke;
}
.pending-text {
  font-size: 28rpx;
  font-weight: 700;
  color: $ln-primary;
}
.save-all {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 28rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #fff;
  background: $ln-primary;
  @include brutal-box($ln-r-md, $ln-bw-thin);
}

/* 待发送图片 */
.pending-images {
  display: flex;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  background: $ln-card;
  border-top: $ln-bw-thin solid $ln-stroke;
}
.pi-item {
  position: relative;
  padding: 10rpx 10rpx 0 0;
}
.pi-thumb {
  width: 144rpx;
  height: 144rpx;
  border: $ln-bw-thin solid $ln-stroke;
  border-radius: $ln-r-sm;
}
.pi-remove {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40rpx;
  height: 40rpx;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
}

/* 输入栏 */
.composer {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx;
  background: $ln-card;
  border-top: $ln-bw-thin solid $ln-stroke;
}
.media-btn,
.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 96rpx;
  height: 96rpx;
  background: $ln-bg;
  @include brutal-box($ln-r-md, $ln-bw-thin);
  &:active {
    background: $ln-accent;
  }
}
.send-btn {
  background: $ln-success;
  &.off {
    opacity: 0.5;
  }
}
.input-wrap {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  min-height: 96rpx;
  padding: 0 28rpx;
  background: $ln-bg;
  @include brutal-box($ln-r-md, $ln-bw-thin);
}
.input {
  width: 100%;
  font-size: 30rpx;
  font-weight: 600;
}
.ph {
  color: $ln-text-secondary;
  font-weight: 500;
}
.hold {
  flex: 1;
  min-height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
  background: $ln-bg;
  user-select: none;
  @include brutal-box($ln-r-md, $ln-bw-thin);
  &.active {
    color: #fff;
    background: $ln-primary;
  }
  &.cancel {
    background: $ln-error;
  }
}
</style>
