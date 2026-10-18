<template>
  <view>
    <view v-for="group in groups" :key="group.type" class="card">
      <text class="title">{{ group.label }}</text>
      <view class="grid">
        <view v-for="c in group.items" :key="c.id" class="item">
          <text class="icon">{{ c.icon || '📝' }}</text>
          <text class="muted">{{ c.name }}</text>
        </view>
      </view>
    </view>
    <!-- TODO: 新增自定义分类（对应原项目 AddCategoryModal）、编辑与删除自己的分类 -->
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
}
.icon {
  font-size: 44rpx;
}
</style>
