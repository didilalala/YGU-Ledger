<template>
  <view class="ln-segment">
    <view v-for="opt in options" :key="opt.value" :class="['item', { active: opt.value === modelValue }]"
      @click="select(opt.value)">
      <text>{{ opt.label }}</text>
    </view>
  </view>
</template>

<script setup>
/** 分段控件：白色圆角外框 + 黄色选中块，对应原项目统计页顶部的"资产 / 收支"切换 */
const props = defineProps({
  options: { type: Array, required: true }, // [{ label, value }]
  modelValue: { type: [String, Number], default: null },
})
const emit = defineEmits(['update:modelValue', 'change'])

function select(value) {
  if (value === props.modelValue) return
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style lang="scss" scoped>
.ln-segment {
  display: flex;
  padding: 6rpx;
  background: $ln-card;
  @include brutal-box($ln-r-lg);
}
.item {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  border: $ln-bw-thin solid transparent; // 始终占位，避免切换时尺寸跳动
  border-radius: $ln-r-md;
  font-size: 30rpx;
  font-weight: 800;
  color: $ln-text-secondary;
  &.active {
    background: $ln-accent;
    border-color: $ln-stroke;
    color: $ln-text;
  }
}
</style>
