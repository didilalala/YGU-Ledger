<template>
  <view class="page has-tabbar">
    <view class="profile" @click="go('/pages/mine/profile')">
      <view class="avatar-box">
        <image v-if="userStore.user?.avatar" class="avatar" :src="userStore.user.avatar" mode="aspectFill" />
        <ln-icon v-else name="user" :size="56" />
      </view>
      <view class="info">
        <text class="name">{{ userStore.displayName || '用户' }}</text>
        <text class="sub">{{ userStore.user?.email || '智能记账用户' }}</text>
      </view>
      <ln-icon name="chevron-right" :size="44" />
    </view>

    <view v-for="group in groups" :key="group.title" class="group">
      <text class="group-title">{{ group.title }}</text>
      <view v-for="item in group.items" :key="item.label" class="item" @click="item.action()">
        <view class="item-left">
          <view class="icon-box" :style="{ background: item.color }"><ln-icon :name="item.icon" :size="38" /></view>
          <text class="item-label">{{ item.label }}</text>
        </view>
        <ln-icon name="chevron-right" :size="38" color="#6F6A9C" />
      </view>
    </view>

    <view class="logout" @click="userStore.logout()">
      <ln-icon name="log-out" :size="38" color="#FF7A6E" />
      <text>退出登录</text>
    </view>

    <view class="version">
      <text class="mono">版本 {{ version }}</text>
      <text class="mono">© 2026 LiteNote</text>
    </view>

    <ln-tabbar current="mine" />
  </view>
</template>

<script setup>
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { checkUpdate } from '@/utils/update'

const userStore = useUserStore()

onShow(() => userStore.refreshProfile().catch(() => {}))

const go = (url) => uni.navigateTo({ url })

let version = 'H5'
// #ifdef APP-PLUS
version = uni.getAppBaseInfo().appVersion || ''
// #endif

// 分组、图标块配色与原项目 SettingsScreen 一致
const groups = [
  {
    title: '💰 财务',
    items: [
      { label: '账户管理', icon: 'credit-card', color: '#7ADBB0', action: () => go('/pages/account/index') },
      { label: '预算管理', icon: 'wallet', color: '#FFD86B', action: () => go('/pages/budget/index') },
      { label: '财务目标', icon: 'target', color: '#FF9EC4', action: () => go('/pages/goal/index') },
      { label: '分类管理', icon: 'folder', color: '#FFAE7A', action: () => go('/pages/category/index') },
    ],
  },
  {
    title: '⚙️ 应用',
    items: [
      { label: 'AI 模型配置', icon: 'message-circle', color: '#8FC0FA', action: () => go('/pages/ai/config') },
      // #ifdef APP-PLUS
      { label: '通知自动记账', icon: 'bell', color: '#FFD86B', action: () => go('/pages/mine/notification') },
      // #endif
      { label: '修改密码', icon: 'lock', color: '#B79CF5', action: () => go('/pages/mine/password') },
    ],
  },
  {
    title: 'ℹ️ 关于',
    items: [{ label: '检测升级', icon: 'download', color: '#FFAE7A', action: () => checkUpdate() }],
  },
]
</script>

<style lang="scss" scoped>
.page {
  padding: calc(var(--status-bar-height) + 32rpx) 32rpx 0;
}
.profile {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 32rpx;
  background: $ln-card;
  @include clay-box($ln-r-lg, 10rpx);
  @include clay-press(10rpx);
}
.avatar-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 128rpx;
  height: 128rpx;
  overflow: hidden;
  background: $ln-accent;
  @include clay-box($ln-r-md, 8rpx);
}
.avatar {
  width: 100%;
  height: 100%;
}
.info {
  flex: 1;
}
.name {
  display: block;
  font-size: 36rpx;
  font-weight: 800;
}
.sub {
  display: block;
  margin-top: 4rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
.group {
  margin-top: 36rpx;
}
.group-title {
  display: block;
  margin: 0 8rpx 16rpx;
  font-size: 28rpx;
  font-weight: 800;
  color: $ln-text-secondary;
}
.item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 112rpx;
  padding: 16rpx 24rpx;
  margin-bottom: 16rpx;
  background: $ln-card;
  @include clay-box($ln-r-lg, 6rpx);
  @include clay-press(6rpx);
}
.item-left {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  @include clay-box($ln-r-sm, 6rpx);
}
.item-label {
  font-size: 30rpx;
  font-weight: 700;
}
.logout {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  min-height: 96rpx;
  margin-top: 40rpx;
  font-size: 30rpx;
  font-weight: 800;
  color: $ln-error;
  background: $ln-expense-bg;
  @include clay-box($ln-r-md, 6rpx);
  @include clay-press(6rpx);
}
.version {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 32rpx 0;
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
</style>
