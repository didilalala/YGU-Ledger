<template>
  <view class="ln-segment">
    <view v-for="opt in options" :key="opt.value" :class="['item', { active: opt.value === modelValue }]"
      @click="select(opt.value)">
      <text>{{ opt.label }}</text>
    </view>
  </view>
</template>

<script setup>
/** 分段控件：凹进去的槽 + 凸起的奶黄色选中块，对应原项目统计页顶部的"资产 / 收支"切换 */
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
  padding: 8rpx;
  background: $ln-primary-light;
  border-radius: $ln-r-lg;
  @include clay-inset(6rpx);
}
.item {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  border-radius: $ln-r-md;
  transition: background 0.2s;
  font-size: 30rpx;
  font-weight: 800;
  color: $ln-text-secondary;
  &.active {
    background: $ln-accent;
    color: $ln-text;
    @include clay-shadow(4rpx);
  }
}
</style>
