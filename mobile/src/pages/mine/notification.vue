<template>
  <view class="page">
    <ln-navbar title="通知自动记账" />

    <view class="panel">
      <view class="p-head">
        <view class="p-icon"><ln-icon name="bell" :size="44" /></view>
        <view class="p-text">
          <text class="p-title">支付自动记账</text>
          <text class="p-sub">开启后，微信/支付宝支付时自动弹出记账确认窗口</text>
        </view>
      </view>
      <view class="line" />

      <view class="perm">
        <text class="perm-label">通知监听权限</text>
        <text :class="['status', enabled ? 'on' : 'off']">{{ enabled ? '✓ 已开启' : '未开启' }}</text>
        <view class="mini" @click="refresh"><text>刷新</text></view>
      </view>
      <view v-if="!enabled" class="open-btn btn btn-accent btn-sm" @click="openSettings">去系统设置开启</view>
      <view class="line" />

      <view class="perm">
        <view class="grow">
          <text class="perm-label">自动记账</text>
          <text class="hint">识别到支付通知时先弹窗确认，再入账</text>
        </view>
        <switch :checked="listening" :disabled="!enabled" color="#8F78E6" @change="toggle" />
      </view>
      <text class="tip">通知内容只在本机解析。部分手机还需要在电池设置中允许 LiteNote 后台运行，否则可能漏记。</text>
    </view>

    <!-- 仅开发模式：不过滤包名、不经过解析器，显示收到的每一条通知，用于验证插件链路和收集真实通知文本 -->
    <view v-if="isDev" class="panel">
      <text class="log-title">原始通知（调试）</text>
      <view v-if="!rawLogs.length" class="log muted">暂无。开启自动记账后，任何应用的通知都会出现在这里</view>
      <view v-for="(log, i) in rawLogs" :key="i" class="log mono">{{ log }}</view>
    </view>

    <view v-if="logs.length" class="panel">
      <text class="log-title">最近识别</text>
      <view v-for="(log, i) in logs" :key="i" class="log mono">{{ log }}</view>
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

function refresh() {
  enabled.value = hasListenerPermission()
  listening.value = isAutoRecordRunning()
}
onShow(refresh)

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
.panel {
  padding: 32rpx;
  margin: 32rpx;
  background: $ln-card;
  @include clay-box($ln-r-lg);
}
.p-head {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.p-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 96rpx;
  height: 96rpx;
  background: $ln-accent;
  @include clay-box($ln-r-md, 6rpx);
}
.p-title {
  display: block;
  font-size: 38rpx;
  font-weight: 800;
}
.p-sub {
  display: block;
  margin-top: 4rpx;
  font-size: 26rpx;
  color: $ln-text-secondary;
}
.line {
  height: $ln-bw-thin;
  margin: 28rpx 0;
  background: $ln-divider;
}
.perm {
  display: flex;
  align-items: center;
  gap: 20rpx;
}
.perm-label {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
}
.grow {
  flex: 1;
}
.hint {
  display: block;
  margin-top: 4rpx;
  font-size: 24rpx;
  color: $ln-text-secondary;
}
.status {
  padding: 6rpx 20rpx;
  font-size: 26rpx;
  font-weight: 800;
  border-radius: $ln-r-sm;
  &.on {
    color: #fff;
    background: $ln-success;
  }
  &.off {
    color: $ln-expense;
    background: $ln-expense-bg;
  }
}
.mini {
  margin-left: auto;
  padding: 10rpx 28rpx;
  font-size: 26rpx;
  font-weight: 800;
  background: $ln-card;
  @include clay-box($ln-r-sm, $ln-bw-thin);
  @include clay-press($ln-bw-thin);
}
.open-btn {
  margin-top: 20rpx;
}
.tip {
  display: block;
  margin-top: 20rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: $ln-text-secondary;
}
.log-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 32rpx;
  font-weight: 800;
}
.log {
  padding: 12rpx 0;
  font-size: 24rpx;
  border-bottom: 2rpx solid $ln-divider;
  word-break: break-all;
}
</style>
