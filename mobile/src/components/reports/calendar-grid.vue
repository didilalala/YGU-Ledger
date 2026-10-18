<template>
  <view class="calendar">
    <view class="week">
      <text v-for="d in WEEK_DAYS" :key="d" class="week-day">{{ d }}</text>
    </view>
    <view class="grid">
      <view v-for="cell in cells" :key="cell.key" class="slot">
        <grid-cell v-if="!cell.empty" :label="String(cell.day)" :income="cell.income" :expense="cell.expense"
          :selected="selected === cell.dateStr" :current="cell.isToday" :disabled="cell.isFuture"
          @press="$emit('select', cell.dateStr)" />
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { WEEK_DAYS, buildCalendarCells, todayString } from '@/utils/report'
import GridCell from './grid-cell.vue'

const props = defineProps({
  year: { type: Number, required: true },
  month0: { type: Number, required: true }, // 0 起始
  dailyMap: { type: Object, default: () => ({}) },
  selected: { type: String, default: '' },
})
defineEmits(['select'])

const cells = computed(() => buildCalendarCells(props.year, props.month0, props.dailyMap, todayString()))
</script>

<style lang="scss" scoped>
.week {
  display: flex;
  margin-bottom: 12rpx;
}
.week-day {
  flex: 1;
  text-align: center;
  font-size: 28rpx;
  font-weight: 700;
  color: $ln-text-secondary;
}
.grid {
  display: flex;
  flex-wrap: wrap;
}
/* 7 列，格子保持正方形：宽度 1/7，用 padding-top 撑出等高 */
.slot {
  position: relative;
  width: 14.2857%;
  padding: 0 3rpx 6rpx;
  &::before {
    content: '';
    display: block;
    padding-top: 100%;
  }
  > * {
    position: absolute;
    top: 0;
    left: 3rpx;
    right: 3rpx;
    bottom: 6rpx;
    width: auto;
    height: auto;
  }
}
</style>
