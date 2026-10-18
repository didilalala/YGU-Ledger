<template>
  <view class="page">
    <ln-navbar title="预算管理">
      <template #right><view class="add-btn" @click="edit()"><ln-icon name="plus" :size="40" :stroke="3" /></view></template>
    </ln-navbar>

    <view class="summary">
      <view class="s-item"><text class="s-num mono">{{ budgets.length }}</text><text class="s-label">个预算</text></view>
      <view class="s-div" />
      <view class="s-item"><text class="s-num mono">{{ activeCount }}</text><text class="s-label">进行中</text></view>
      <view class="s-div" />
      <view class="s-item"><text :class="['s-num mono', { over: overCount > 0 }]">{{ overCount }}</text><text class="s-label">已超支</text></view>
    </view>

    <view class="list">
      <view v-for="b in budgets" :key="b.id" :class="['card-b', { off: !b.isActive }]">
        <view class="b-head">
          <view class="b-title">
            <view class="b-icon" :style="{ background: iconColor(b) }"><text>{{ iconOf(b) }}</text></view>
            <view class="b-names">
              <text class="b-name">{{ b.name }}</text>
              <text class="b-cat">{{ categoryName(b) }}</text>
            </view>
          </view>
          <view class="badges">
            <text class="period">{{ b.period === 'monthly' ? '本月' : '本年' }}</text>
            <text v-if="!b.isActive" class="badge">已停用</text>
            <text v-else :class="['badge', { over: b.isOverBudget }]">{{ Math.round(b.percentage) }}%</text>
          </view>
        </view>

        <template v-if="b.isActive">
          <ln-progress :percent="Math.min(b.percentage, 100)" :color="b.isOverBudget ? '#EF4444' : b.isAlert ? '#F97316' : '#3B82F6'" :height="28" />
          <view class="amounts mono">
            <text class="spent">已用 ¥{{ formatMoney(b.spent) }}</text>
            <text class="total">/ 预算 ¥{{ formatMoney(b.amount) }}</text>
          </view>
          <view v-if="b.isOverBudget" class="warning"><text>超支 ¥{{ formatMoney(Math.abs(b.remaining)) }}</text></view>
        </template>
        <view v-else class="amounts mono"><text class="total">预算 ¥{{ formatMoney(b.amount) }} / {{ b.period === 'monthly' ? '每月' : '每年' }}</text></view>

        <view class="actions">
          <view class="edit-btn" @click="edit(b.id)"><ln-icon name="pencil" :size="30" /><text>编辑</text></view>
        </view>
      </view>

      <view v-if="loaded && !budgets.length" class="empty">
        <text class="empty-icon">💰</text>
        <text class="empty-text">还没有预算计划</text>
        <text class="empty-sub">创建预算，合理控制你的开支</text>
        <view class="btn btn-primary btn-sm" @click="edit()">创建预算</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { budgetApi } from '@/api'
import { useCategoryStore } from '@/stores/category'
import { categoryColor } from '@/utils/category-style'
import { formatMoney } from '@/utils/format'

const categoryStore = useCategoryStore()
const budgets = ref([])
const loaded = ref(false)

const activeCount = computed(() => budgets.value.filter((b) => b.isActive).length)
const overCount = computed(() => budgets.value.filter((b) => b.isActive && b.isOverBudget).length)

async function load() {
  // progress 只包含启用的预算，停用的要从 list 补上，否则无法重新启用
  const [all, progress] = await Promise.all([budgetApi.list(), budgetApi.progress(), categoryStore.load()])
  const byId = new Map(progress.map((p) => [p.id, p]))
  budgets.value = all.map((b) => byId.get(b.id) || b)
  loaded.value = true
}
onShow(() => load().catch(() => {}))
onPullDownRefresh(async () => {
  await load().catch(() => {})
  uni.stopPullDownRefresh()
})

const categoryOf = (b) => b.categoryId && categoryStore.list.find((x) => x.id === b.categoryId)
const categoryName = (b) => categoryOf(b)?.name || '总预算'
const iconOf = (b) => categoryOf(b)?.icon || '📊'
const iconColor = (b) => (categoryOf(b) ? categoryColor(categoryOf(b).name) : '#3B82F6')

const edit = (id) => uni.navigateTo({ url: `/pages/budget/edit${id ? `?id=${id}` : ''}` })
</script>

<style lang="scss" scoped>
.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  background: $ln-accent;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
  &:active {
    background: #eab308;
  }
}
.summary {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  background: $ln-card;
  border-bottom: $ln-bw-thin solid $ln-stroke;
}
.s-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.s-num {
  font-size: 44rpx;
  font-weight: 900;
  &.over {
    color: $ln-error;
  }
}
.s-label {
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
.s-div {
  width: $ln-bw-thin;
  height: 56rpx;
  background: $ln-border;
}
.list {
  padding: 32rpx;
}
.card-b {
  padding: 32rpx;
  margin: 0 8rpx 36rpx 0;
  background: $ln-card;
  @include brutal-box($ln-r-lg);
  @include brutal-shadow(8rpx);
  &.off {
    opacity: 0.65;
  }
}
.b-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28rpx;
}
.b-title {
  display: flex;
  align-items: center;
  gap: 20rpx;
  min-width: 0;
}
.b-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 88rpx;
  height: 88rpx;
  font-size: 42rpx;
  @include brutal-box($ln-r-md, $ln-bw-thin);
}
.b-name {
  display: block;
  font-size: 32rpx;
  font-weight: 800;
}
.b-cat {
  display: block;
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
.badges {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.period {
  padding: 4rpx 16rpx;
  font-size: 22rpx;
  font-weight: 700;
  background: $ln-primary-light;
  border: $ln-bw-thin solid $ln-stroke;
  border-radius: 12rpx;
}
.badge.over {
  color: #fff;
  background: $ln-error;
}
.amounts {
  display: flex;
  gap: 12rpx;
  margin-top: 20rpx;
  font-size: 26rpx;
  font-weight: 700;
}
.spent {
  color: $ln-text;
}
.total {
  color: $ln-text-secondary;
}
.warning {
  margin-top: 20rpx;
  padding: 12rpx 20rpx;
  font-size: 26rpx;
  font-weight: 800;
  color: $ln-error;
  background: $ln-expense-bg;
  border: $ln-bw-thin solid $ln-error;
  border-radius: $ln-r-sm;
}
.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 28rpx;
}
.edit-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 28rpx;
  font-size: 26rpx;
  font-weight: 800;
  background: $ln-card;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
  @include brutal-shadow(4rpx);
  @include brutal-press(4rpx);
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  padding: 120rpx 0;
}
.empty-icon {
  font-size: 96rpx;
}
.empty-text {
  font-size: 32rpx;
  font-weight: 800;
  color: $ln-text-secondary;
}
.empty-sub {
  margin-bottom: 16rpx;
  font-size: 26rpx;
  color: $ln-text-secondary;
}
</style>
