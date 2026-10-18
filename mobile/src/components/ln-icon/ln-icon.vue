<template>
  <view class="ln-icon" :style="style" />
</template>

<script setup>
import { computed } from 'vue'
import { iconUri } from '@/utils/icons'

const props = defineProps({
  name: { type: String, required: true },
  /** 边长，单位 rpx */
  size: { type: Number, default: 40 },
  color: { type: String, default: '#1A1A1A' },
  stroke: { type: Number, default: 2.5 },
})

const style = computed(() => {
  const uri = iconUri(props.name, props.color, props.stroke)
  return {
    width: `${props.size}rpx`,
    height: `${props.size}rpx`,
    backgroundImage: uri ? `url("${uri}")` : 'none',
  }
})
</script>

<style scoped>
.ln-icon {
  display: inline-block;
  flex-shrink: 0;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
}
</style>
