<template>
  <view class="period-nav">
    <view class="arrow" @click="$emit('prev')"><ln-icon name="chevron-left" :size="40" /></view>
    <text class="title">{{ title }}</text>
    <view :class="['arrow', { disabled: disableNext }]" @click="!disableNext && $emit('next')">
      <ln-icon name="chevron-right" :size="40" :color="disableNext ? '#A3A3A3' : '#1A1A1A'" />
    </view>
  </view>
</template>

<script setup>
/** 周期导航：左右带描边的箭头按钮 + 居中的加粗标题，对应原项目 PeriodNavigator */
defineProps({
  title: { type: String, required: true },
  disableNext: { type: Boolean, default: false },
})
defineEmits(['prev', 'next'])
</script>

<style lang="scss" scoped>
.period-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8rpx 80rpx 32rpx;
}
.arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96rpx;
  height: 96rpx;
  background: $ln-card;
  @include brutal-box($ln-r-md);
  &.disabled {
    background: transparent;
    border-color: $ln-border;
  }
  &:not(.disabled):active {
    background: $ln-accent;
  }
}
.title {
  font-size: 44rpx;
  font-weight: 800;
}
</style>
