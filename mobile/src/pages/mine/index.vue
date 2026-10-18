<template>
  <view>
    <view class="card profile">
      <image v-if="userStore.user?.avatar" class="avatar" :src="userStore.user.avatar" mode="aspectFill" />
      <view v-else class="avatar placeholder">{{ userStore.displayName.slice(0, 1) }}</view>
      <view class="info">
        <text class="name">{{ userStore.displayName }}</text>
        <text class="muted">@{{ userStore.user?.username }}</text>
      </view>
    </view>

    <uni-list class="menu">
      <uni-list-item title="预算" show-arrow clickable @click="go('/pages/budget/index')" />
      <uni-list-item title="财务目标" show-arrow clickable @click="go('/pages/goal/index')" />
      <uni-list-item title="分类管理" show-arrow clickable @click="go('/pages/category/index')" />
      <!-- #ifdef APP-PLUS -->
      <uni-list-item title="通知自动记账" show-arrow clickable @click="go('/pages/mine/notification')" />
      <!-- #endif -->
      <!-- TODO: AI 模型配置、编辑资料、修改密码、检查更新 -->
    </uni-list>

    <view class="actions">
      <button @click="userStore.logout()">退出登录</button>
    </view>
  </view>
</template>

<script setup>
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onShow(() => userStore.refreshProfile().catch(() => {}))

const go = (url) => uni.navigateTo({ url })
</script>

<style lang="scss" scoped>
.profile {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.avatar {
  width: 112rpx;
  height: 112rpx;
  border-radius: 50%;
  &.placeholder {
    background: $ln-primary;
    color: #fff;
    font-size: 48rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
.info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.name {
  font-size: 36rpx;
  font-weight: 600;
}
.menu {
  margin: 24rpx 32rpx;
  display: block;
  border-radius: 24rpx;
  overflow: hidden;
}
.actions {
  padding: 32rpx;
}
</style>
