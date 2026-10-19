<template>
  <view class="track" :style="{ height: height + 'rpx' }">
    <view class="fill" :style="{ width: clamped + '%', background: color }" />
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  percent: { type: Number, default: 0 },
  color: { type: String, default: '#8F78E6' },
  height: { type: Number, default: 36 },
})
const clamped = computed(() => Math.max(0, Math.min(100, Number(props.percent) || 0)))
</script>

<style lang="scss" scoped>
.track {
  padding: 4rpx;
  background: $ln-primary-light;
  border-radius: 999rpx;
  @include clay-inset(4rpx);
}
/* 凹槽里一根凸起的黏土条 */
.fill {
  height: 100%;
  min-width: 0;
  border-radius: 999rpx;
  transition: width 0.3s;
  @include clay-shadow(2rpx);
}
</style>
