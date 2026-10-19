<template>
  <view class="ln-tabbar-wrap">
    <view class="ln-tabbar">
      <view v-for="tab in LEFT" :key="tab.key" class="tab" @click="go(tab)">
        <view :class="['icon-box', { active: current === tab.key }]">
          <ln-icon :name="tab.icon" :size="40" :color="current === tab.key ? '#2F2A5C' : '#A9A4CF'" />
        </view>
        <text :class="['label', { active: current === tab.key }]">{{ tab.label }}</text>
      </view>

      <view class="tab add" @click="add">
        <view class="add-btn"><ln-icon name="plus" :size="48" :stroke="4" color="#FFFFFF" /></view>
        <text class="label">记账</text>
      </view>

      <view v-for="tab in RIGHT" :key="tab.key" class="tab" @click="go(tab)">
        <view :class="['icon-box', { active: current === tab.key }]">
          <ln-icon :name="tab.icon" :size="40" :color="current === tab.key ? '#2F2A5C' : '#A9A4CF'" />
        </view>
        <text :class="['label', { active: current === tab.key }]">{{ tab.label }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted } from 'vue'

/**
 * 自绘底部导航：5 个位置，中间是凸起的珊瑚色"记账"按钮（黏土风格，对应原项目 AppNavigator）。
 * 原生 tabBar 仍保留在 pages.json 里（switchTab 需要它，并且能让各 tab 页面保持状态），这里把它隐藏。
 */
defineProps({ current: { type: String, default: '' } })

const LEFT = [
  { key: 'dashboard', label: '首页', icon: 'home', url: '/pages/dashboard/index' },
  { key: 'reports', label: '统计', icon: 'bar-chart', url: '/pages/reports/index' },
]
const RIGHT = [
  { key: 'chat', label: 'AI助手', icon: 'message-circle', url: '/pages/ai/chat' },
  { key: 'mine', label: '我的', icon: 'user', url: '/pages/mine/index' },
]

onMounted(() => uni.hideTabBar({ animation: false, fail: () => {} }))

const go = (tab) => uni.switchTab({ url: tab.url })
const add = () => uni.navigateTo({ url: '/pages/bills/create' })
</script>

<style lang="scss" scoped>
.ln-tabbar-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  background: $ln-card;
  border-radius: $ln-r-lg $ln-r-lg 0 0;
  box-shadow: 0 -10rpx 36rpx rgba(120, 100, 190, 0.18);
  padding-bottom: env(safe-area-inset-bottom);
}
.ln-tabbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 132rpx;
  padding: 0 16rpx 14rpx;
}
.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
}
.icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 76rpx;
  height: 76rpx;
  border-radius: $ln-r-sm;
  &.active {
    background: $ln-sky;
    @include clay-shadow(4rpx);
  }
}
.label {
  font-size: 22rpx;
  font-weight: 600;
  color: $ln-text-secondary;
  &.active {
    color: $ln-text;
    font-weight: 800;
  }
}
.add {
  position: relative;
}
.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 112rpx;
  height: 112rpx;
  margin-top: -52rpx;
  background: #ff9a8b;
  @include clay-box($ln-r-md, 8rpx);
  @include clay-press(8rpx);
}
</style>
