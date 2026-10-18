<template>
  <view class="ln-navbar" :style="{ paddingTop: statusBar + 'px' }">
    <view class="bar">
      <view class="side">
        <view v-if="back" class="icon-btn" @click="goBack"><ln-icon name="chevron-left" :size="40" /></view>
        <slot name="left" />
      </view>
      <text class="title">{{ title }}</text>
      <view class="side right"><slot name="right" /></view>
    </view>
  </view>
</template>

<script setup>
/**
 * 自绘导航栏：白底 + 底部粗黑线，标题居中加粗，左右各有一个带描边的图标按钮位。
 * 全局关闭了原生导航栏（pages.json 的 navigationStyle: custom），所有页面统一用它，H5 与 App 外观一致。
 */
const props = defineProps({
  title: { type: String, default: '' },
  back: { type: Boolean, default: true },
})

const statusBar = uni.getSystemInfoSync().statusBarHeight || 0

function goBack() {
  // 直接打开某个页面（刷新 / 深链）时没有上一页，回首页
  if (getCurrentPages().length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/dashboard/index' })
}
</script>

<style lang="scss" scoped>
.ln-navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: $ln-card;
  border-bottom: $ln-bw solid $ln-stroke;
}
.bar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 104rpx;
  padding: 0 32rpx;
}
.title {
  position: absolute;
  left: 140rpx;
  right: 140rpx;
  text-align: center;
  font-size: 36rpx;
  font-weight: 800;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.side {
  display: flex;
  align-items: center;
  gap: 16rpx;
  min-width: 72rpx;
  &.right {
    justify-content: flex-end;
  }
}
.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  background: $ln-card;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
}
</style>
