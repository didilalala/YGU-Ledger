<template>
  <view>
    <view class="card">
      <view class="row">
        <text>通知使用权</text>
        <text :class="enabled ? 'income' : 'expense'">{{ enabled ? '已开启' : '未开启' }}</text>
      </view>
      <button v-if="!enabled" size="mini" @click="openSettings">去开启</button>
      <text class="muted tip">
        开启后，LiteNote 会读取微信、支付宝的支付通知并自动记账。通知内容只在本机解析。
        部分手机还需要在电池设置中允许 LiteNote 后台运行，否则可能漏记。
      </text>
    </view>

    <view class="card">
      <view class="row">
        <text>自动记账</text>
        <switch :checked="listening" :disabled="!enabled" @change="toggle" />
      </view>
    </view>

    <!-- 仅开发模式：不过滤包名、不经过解析器，显示收到的每一条通知，用于验证插件链路和收集真实通知文本 -->
    <view v-if="isDev" class="card">
      <text class="title">原始通知（调试）</text>
      <view v-if="!rawLogs.length" class="muted log">暂无。开启自动记账后，任何应用的通知都会出现在这里</view>
      <view v-for="(log, i) in rawLogs" :key="i" class="muted log">{{ log }}</view>
    </view>

    <view v-if="logs.length" class="card">
      <text class="title">最近识别</text>
      <view v-for="(log, i) in logs" :key="i" class="muted log">{{ log }}</view>
    </view>
  </view>
</template>

<script setup>
import { onUnmounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  hasListenerPermission, isAutoRecordRunning, onAutoRecordEvent, startAutoRecord, stopAutoRecord,
} from '@/services/notification/auto-record'
// #ifdef APP-ANDROID
import { openListenerSettings } from '@/uni_modules/lite-notification-listener'
// #endif

const enabled = ref(false) // 系统是否已授予通知使用权
const listening = ref(false)
const logs = ref([])
const rawLogs = ref([])
const isDev = import.meta.env.DEV

const STATUS_TEXT = { saved: '已记账', skipped: '已忽略', failed: '记账失败' }

// 记账和确认弹窗由服务处理（离开本页也生效），这里只订阅事件来展示最近的识别结果
const off = onAutoRecordEvent((evt) => {
  if (evt.kind === 'raw') {
    rawLogs.value.unshift(`[${evt.info.pkg}] ${evt.info.title} | ${evt.info.text}`)
  } else {
    const { bill } = evt
    logs.value.unshift(`${bill.date} ${bill.type === 'income' ? '+' : '-'}${bill.amount} ${bill.description}（${STATUS_TEXT[evt.status]}）`)
  }
})
onUnmounted(off)

onShow(() => {
  enabled.value = hasListenerPermission()
  listening.value = isAutoRecordRunning()
})

function openSettings() {
  // #ifdef APP-ANDROID
  openListenerSettings()
  // #endif
}

function toggle(e) {
  if (e.detail.value) {
    listening.value = startAutoRecord()
    if (!listening.value) uni.showToast({ title: '请先开启通知使用权', icon: 'none' })
  } else {
    stopAutoRecord()
    listening.value = false
  }
}
</script>

<style lang="scss" scoped>
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.tip {
  display: block;
  margin-top: 16rpx;
  line-height: 1.6;
}
.title {
  font-weight: 600;
}
.log {
  padding: 8rpx 0;
}
</style>
