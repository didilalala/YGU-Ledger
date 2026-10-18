<template>
  <view class="page">
    <ln-navbar title="分类管理" />

    <view class="seg"><ln-segment v-model="type" :options="TYPES" /></view>

    <view class="grid">
      <view v-for="c in items" :key="c.id" :class="['cat', { mine: !c.isDefault }]" @click="open(c)">
        <view class="cat-icon" :style="{ background: categoryColor(c.name) }"><text>{{ c.icon || '📝' }}</text></view>
        <text class="cat-name">{{ c.name }}</text>
        <text v-if="!c.isDefault" class="cat-tag">自定义</text>
      </view>
      <view class="cat add" @click="edit(null)">
        <view class="cat-icon add-icon"><ln-icon name="plus" :size="44" :stroke="3" /></view>
        <text class="cat-name">添加</text>
      </view>
    </view>

    <text class="tip">点击自己添加的分类可以编辑或删除；系统默认分类不能修改</text>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useCategoryStore } from '@/stores/category'
import { categoryColor } from '@/utils/category-style'

const TYPES = [
  { value: 'expense', label: '支出分类' },
  { value: 'income', label: '收入分类' },
]
const store = useCategoryStore()
const type = ref('expense')
const items = computed(() => (type.value === 'expense' ? store.expense : store.income))

onShow(() => store.load(true).catch(() => {}))

const edit = (id) => uni.navigateTo({ url: `/pages/category/edit?${id ? `id=${id}` : `type=${type.value}`}` })

function open(c) {
  if (c.isDefault) return uni.showToast({ title: '系统默认分类不能修改', icon: 'none' })
  edit(c.id)
}
</script>

<style lang="scss" scoped>
.seg {
  padding: 32rpx;
}
.grid {
  display: flex;
  flex-wrap: wrap;
  gap: 24rpx;
  padding: 0 32rpx;
}
.cat {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  width: calc((100% - 72rpx) / 4);
  padding: 24rpx 0 20rpx;
  background: $ln-card;
  @include brutal-box($ln-r-md, $ln-bw-thin);
  &:active {
    background: $ln-bg;
  }
  &.add {
    border-style: dashed;
  }
}
.cat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  font-size: 40rpx;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
  &.add-icon {
    background: $ln-accent;
  }
}
.cat-name {
  max-width: 100%;
  padding: 0 8rpx;
  font-size: 24rpx;
  font-weight: 700;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.cat-tag {
  position: absolute;
  top: -14rpx;
  right: -8rpx;
  padding: 0 10rpx;
  font-size: 18rpx;
  font-weight: 800;
  background: $ln-primary-light;
  border: 3rpx solid $ln-stroke;
  border-radius: 10rpx;
}
.tip {
  display: block;
  padding: 40rpx 32rpx;
  text-align: center;
  font-size: 24rpx;
  color: $ln-text-secondary;
}
</style>
