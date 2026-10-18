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
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { billApi } from '@/api'
import { createDeduplicator, PACKAGES, parseNotification } from '@/services/notification/parser'
// #ifdef APP-ANDROID
import { isListenerEnabled, openListenerSettings, startListening, stopListening } from '@/uni_modules/lite-notification-listener'
// #endif

const enabled = ref(false)
const listening = ref(false)
const logs = ref([])
const rawLogs = ref([])
const isDev = import.meta.env.DEV
const isDuplicate = createDeduplicator()

onShow(() => {
  // #ifdef APP-ANDROID
  enabled.value = isListenerEnabled()
  // #endif
})

function openSettings() {
  // #ifdef APP-ANDROID
  openListenerSettings()
  // #endif
}

async function onNotification(info) {
  if (isDev) rawLogs.value.unshift(`[${info.pkg}] ${info.title} | ${info.text}`)
  const bill = parseNotification(info)
  if (!bill || isDuplicate(bill)) return
  logs.value.unshift(`${bill.date} ${bill.type === 'income' ? '+' : '-'}${bill.amount} ${bill.description}`)
  // TODO: 先弹窗让用户确认/选择分类再记账（原项目有"自动记账弹窗"）
  const { raw, ...data } = bill
  await billApi.create({ ...data, notes: raw }).catch(() => {})
}

function toggle(e) {
  listening.value = e.detail.value
  // #ifdef APP-ANDROID
  if (listening.value) startListening({ packages: isDev ? [] : [PACKAGES.WECHAT, PACKAGES.ALIPAY] }, onNotification)
  else stopListening()
  // #endif
  // TODO: 把开关状态存入 storage，App.vue 启动时自动恢复监听
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
