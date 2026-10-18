<template>
  <view class="track" :style="{ height: height + 'rpx' }">
    <view class="fill" :style="{ width: clamped + '%', background: color }" />
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  percent: { type: Number, default: 0 },
  color: { type: String, default: '#3B82F6' },
  height: { type: Number, default: 36 },
})
const clamped = computed(() => Math.max(0, Math.min(100, Number(props.percent) || 0)))
</script>

<style lang="scss" scoped>
.track {
  overflow: hidden;
  background: #e5e7eb;
  border: $ln-bw-thin solid $ln-stroke;
  border-radius: $ln-r-sm;
}
.fill {
  height: 100%;
  border-right: $ln-bw-thin solid $ln-stroke;
  transition: width 0.3s;
  // 0% 时不显示那条右描边
  &[style*='width: 0%'] {
    border-right: none;
  }
}
</style>
