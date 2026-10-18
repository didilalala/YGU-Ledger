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
        <ln-icon name="chevron-right" :size="38" color="#737373" />
      </view>
    </view>

    <view class="logout" @click="userStore.logout()">
      <ln-icon name="log-out" :size="38" color="#EF4444" />
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
      { label: '账户管理', icon: 'credit-card', color: '#7DCEA0', action: () => go('/pages/account/index') },
      { label: '预算管理', icon: 'wallet', color: '#FFD93D', action: () => go('/pages/budget/index') },
      { label: '财务目标', icon: 'target', color: '#FF90B3', action: () => go('/pages/goal/index') },
      { label: '分类管理', icon: 'folder', color: '#FFB366', action: () => go('/pages/category/index') },
    ],
  },
  {
    title: '⚙️ 应用',
    items: [
      { label: 'AI 模型配置', icon: 'message-circle', color: '#7EB6FF', action: () => go('/pages/ai/config') },
      // #ifdef APP-PLUS
      { label: '通知自动记账', icon: 'bell', color: '#FFD93D', action: () => go('/pages/mine/notification') },
      // #endif
      { label: '修改密码', icon: 'lock', color: '#C5A3FF', action: () => go('/pages/mine/password') },
    ],
  },
  {
    title: 'ℹ️ 关于',
    items: [{ label: '检测升级', icon: 'download', color: '#FFB366', action: () => checkUpdate() }],
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
  @include brutal-box($ln-r-lg, $ln-bw-thin);
  @include brutal-shadow(6rpx);
  @include brutal-press(6rpx);
  margin-right: 6rpx;
}
.avatar-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 128rpx;
  height: 128rpx;
  overflow: hidden;
  background: $ln-accent;
  @include brutal-box($ln-r-md);
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
  @include brutal-box($ln-r-lg, $ln-bw-thin);
  &:active {
    background: $ln-bg;
  }
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
  @include brutal-box($ln-r-sm, $ln-bw-thin);
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
  background: rgba(239, 68, 68, 0.08);
  border: $ln-bw-thin solid $ln-error;
  border-radius: $ln-r-md;
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
