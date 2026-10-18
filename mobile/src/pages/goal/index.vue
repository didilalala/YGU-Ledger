<template>
  <view class="page">
    <ln-navbar title="财务目标">
      <template #right><view class="add-btn" @click="edit()"><ln-icon name="plus" :size="40" :stroke="3" /></view></template>
    </ln-navbar>

    <view class="summary">
      <view class="s-item"><text class="s-num mono">{{ goals.length }}</text><text class="s-label">个目标</text></view>
      <view class="s-div" />
      <view class="s-item"><text class="s-num mono">{{ goals.filter((g) => !g.isCompleted).length }}</text><text class="s-label">进行中</text></view>
      <view class="s-div" />
      <view class="s-item"><text class="s-num mono done">{{ goals.filter((g) => g.isCompleted).length }}</text><text class="s-label">已完成</text></view>
    </view>

    <view class="list">
      <view v-for="g in goals" :key="g.id" class="goal" @click="edit(g.id)">
        <view class="g-head">
          <view class="g-title">
            <view class="g-icon"><text>{{ g.icon || '🎯' }}</text></view>
            <view class="g-names">
              <text class="g-name">{{ g.name }}</text>
              <text :class="['g-sub mono', { late: !g.isCompleted && isLate(g.deadline) }]">{{ g.isCompleted ? '已完成 ✓' : deadlineText(g.deadline) || '目标' }}</text>
            </view>
          </view>
          <text :class="['badge', { done: g.isCompleted }]">{{ Math.round(g.progress) }}%</text>
        </view>
        <ln-progress :percent="g.progress" color="#22C55E" :height="28" />
        <view class="amounts mono">
          <text>已存 ¥{{ formatMoney(g.currentAmount) }}</text>
          <text class="muted-text">目标 ¥{{ formatMoney(g.targetAmount) }}</text>
        </view>
      </view>

      <view v-if="loaded && !goals.length" class="empty">
        <text class="empty-icon">🎯</text>
        <text class="empty-text">还没有财务目标</text>
        <text class="empty-sub">设定一个小目标，慢慢攒起来</text>
        <view class="btn btn-primary btn-sm" @click="edit()">创建目标</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { goalApi } from '@/api'
import { daysLeft, deadlineText } from '@/utils/dashboard'
import { formatMoney } from '@/utils/format'

const goals = ref([])
const loaded = ref(false)

async function load() {
  goals.value = await goalApi.list()
  loaded.value = true
}
onShow(() => load().catch(() => {}))
onPullDownRefresh(async () => {
  await load().catch(() => {})
  uni.stopPullDownRefresh()
})

const isLate = (deadline) => daysLeft(deadline) < 0
const edit = (id) => uni.navigateTo({ url: `/pages/goal/edit${id ? `?id=${id}` : ''}` })
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
  &.done {
    color: $ln-income;
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
.goal {
  padding: 32rpx;
  margin: 0 8rpx 36rpx 0;
  background: $ln-card;
  @include brutal-box($ln-r-lg);
  @include brutal-shadow(8rpx);
  @include brutal-press(8rpx);
}
.g-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28rpx;
}
.g-title {
  display: flex;
  align-items: center;
  gap: 20rpx;
  min-width: 0;
}
.g-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 88rpx;
  height: 88rpx;
  font-size: 42rpx;
  background: $ln-accent;
  @include brutal-box($ln-r-md, $ln-bw-thin);
}
.g-name {
  display: block;
  font-size: 32rpx;
  font-weight: 800;
}
.g-sub {
  display: block;
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-text-secondary;
  &.late {
    color: $ln-error;
  }
}
.badge.done {
  background: $ln-income-bg;
  color: $ln-income;
}
.amounts {
  display: flex;
  justify-content: space-between;
  margin-top: 20rpx;
  font-size: 26rpx;
  font-weight: 700;
}
.muted-text {
  color: $ln-text-secondary;
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
