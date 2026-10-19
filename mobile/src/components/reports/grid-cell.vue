<template>
  <view :class="['cell', { selected, current, disabled }]" @click="!disabled && $emit('press')">
    <text class="label">{{ label }}</text>
    <view v-if="!disabled && (income > 0 || expense > 0)" class="amounts">
      <text v-if="income > 0" class="income-text mono">{{ formatCellAmount(income) }}</text>
      <text v-if="expense > 0" class="expense-text mono">{{ formatCellAmount(expense) }}</text>
    </view>
    <text v-else-if="!disabled" class="zero">-</text>
  </view>
</template>

<script setup>
import { formatCellAmount } from '@/utils/report'

/** 日 / 月 / 年网格通用的格子：上面是标签，下面分别是收入（绿）和支出（红） */
defineProps({
  label: { type: String, required: true },
  income: { type: Number, default: 0 },
  expense: { type: Number, default: 0 },
  selected: { type: Boolean, default: false },
  current: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})
defineEmits(['press'])
</script>

<style lang="scss" scoped>
.cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: 100%;
  padding: 4rpx 2rpx;
  background: $ln-card;
  @include clay-box($ln-r-sm, 4rpx);
  &.current:not(.selected) {
    background: $ln-primary-light;
    .label {
      font-weight: 900;
    }
  }
  &.selected {
    background: $ln-primary;
    @include clay-shadow(6rpx);
    .label,
    .income-text,
    .expense-text {
      color: #fff;
    }
    .label {
      font-weight: 900;
    }
  }
  &.disabled {
    opacity: 0.4;
  }
}
.label {
  font-size: 28rpx;
  font-weight: 700;
}
.amounts {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 2rpx;
}
.income-text,
.expense-text {
  font-size: 18rpx;
  font-weight: 700;
  line-height: 1.25;
}
.income-text {
  color: $ln-income;
}
.expense-text {
  color: $ln-expense;
}
.zero {
  margin-top: 2rpx;
  font-size: 18rpx;
  color: $ln-text-quaternary;
}
</style>
