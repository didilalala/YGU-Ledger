<template>
  <view>
    <view v-for="group in groups" :key="group.type" class="card">
      <text class="title">{{ group.label }}</text>
      <view class="grid">
        <view v-for="c in group.items" :key="c.id" :class="['item', { mine: !c.isDefault }]" @click="open(c)">
          <text class="icon">{{ c.icon || '📝' }}</text>
          <text class="muted">{{ c.name }}</text>
        </view>
        <view class="item add" @click="edit(null, group.type)">
          <text class="icon">＋</text>
          <text class="muted">添加</text>
        </view>
      </view>
    </view>
    <view class="muted tip">点击自己添加的分类可以编辑或删除；系统默认分类不能修改</view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useCategoryStore } from '@/stores/category'

const store = useCategoryStore()
const groups = computed(() => [
  { type: 'expense', label: '支出分类', items: store.expense },
  { type: 'income', label: '收入分类', items: store.income },
])

onShow(() => store.load(true).catch(() => {}))

const edit = (id, type) => uni.navigateTo({ url: `/pages/category/edit?${id ? `id=${id}` : `type=${type}`}` })

function open(c) {
  if (c.isDefault) return uni.showToast({ title: '系统默认分类不能修改', icon: 'none' })
  edit(c.id)
}
</script>

<style lang="scss" scoped>
.title {
  font-weight: 600;
}
.grid {
  display: flex;
  flex-wrap: wrap;
  margin-top: 16rpx;
}
.item {
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 0;
  &.add {
    opacity: 0.6;
  }
}
.icon {
  font-size: 44rpx;
}
.tip {
  text-align: center;
  padding: 0 32rpx 32rpx;
}
</style>
