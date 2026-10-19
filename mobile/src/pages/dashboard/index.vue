<template>
  <view class="page has-tabbar">
    <view class="header">
      <view class="title-row">
        <text class="title">{{ monthName }}</text>
        <text class="sticker">✦</text>
      </view>
      <text class="year mono">{{ year }}</text>
    </view>

    <!-- 本月概览：主色块 -->
    <view class="overview">
      <view class="tape"><text>⚡</text></view>
      <text class="ov-label">本月结余</text>
      <text class="ov-balance">¥ {{ fixed(stats.balance) }}</text>
      <view class="ov-divider" />
      <view class="ov-stats">
        <view class="stat" @click="goBills('expense')">
          <view class="stat-icon expense-bg"><ln-icon name="arrow-down-right" :size="32" color="#fff" :stroke="3" /></view>
          <view>
            <text class="stat-label">总支出</text>
            <text class="stat-value">¥ {{ fixed(stats.totalExpense) }}</text>
          </view>
        </view>
        <view class="stat" @click="goBills('income')">
          <view class="stat-icon income-bg"><ln-icon name="arrow-up-right" :size="32" color="#fff" :stroke="3" /></view>
          <view>
            <text class="stat-label">总收入</text>
            <text class="stat-value">¥ {{ fixed(stats.totalIncome) }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 预算与财务目标：可左右滑动 -->
    <view v-if="cards.length" class="cards">
      <swiper class="swiper" :current="cardIndex" :indicator-dots="false" @change="cardIndex = $event.detail.current">
        <swiper-item v-for="c in cards" :key="c.id">
          <view class="progress-card" @click="go(c.url)">
            <view class="pc-head">
              <view class="pc-title">
                <text class="pc-icon">{{ c.icon }}</text>
                <view>
                  <text class="pc-name">{{ c.title }}</text>
                  <text class="pc-type mono">{{ c.typeLabel }}</text>
                </view>
              </view>
              <text class="badge">{{ c.percent }}%</text>
            </view>
            <ln-progress :percent="c.percent" :color="c.color" />
            <view class="pc-labels">
              <text class="mono">{{ c.left }}</text>
              <text class="mono">{{ c.right }}</text>
            </view>
          </view>
        </swiper-item>
      </swiper>
      <view v-if="cards.length > 1" class="dots">
        <view v-for="(c, i) in cards" :key="c.id" :class="['dot', { on: i === cardIndex }]" />
      </view>
    </view>
    <view v-else class="empty-card" @click="go('/pages/budget/index')">
      <text class="empty-icon">📊</text>
      <text class="empty-title">设置预算或财务目标来追踪进度</text>
      <text class="empty-hint">点击前往设置 →</text>
    </view>

    <!-- 近期交易 -->
    <view class="section">
      <view class="section-head">
        <view class="section-title"><text class="sticker-sm">📋</text><text class="st-text">近期交易</text></view>
        <view class="all-btn" @click="goBills()"><text>查看全部</text><ln-icon name="arrow-right" :size="28" :stroke="3" /></view>
      </view>

      <bill-item v-for="bill in recent" :key="bill.id" :bill="bill" @click="goDetail" />

      <view v-if="loaded && !recent.length" class="empty-state">
        <text class="empty-icon">📝</text>
        <text class="empty-title">暂无交易记录</text>
        <view class="btn btn-primary btn-sm" @click="goCreate">添加第一笔</view>
      </view>
    </view>

    <ln-tabbar current="dashboard" />
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { billApi, budgetApi, goalApi } from '@/api'
import { pickBudgets, pickGoals } from '@/utils/dashboard'
import { formatMoney, monthRange } from '@/utils/format'

const stats = ref({ balance: 0, totalIncome: 0, totalExpense: 0 })
const recent = ref([])
const budgets = ref([])
const goals = ref([])
const cardIndex = ref(0)
const loaded = ref(false)

const now = new Date()
const monthName = `${now.getMonth() + 1}月账本`
const year = String(now.getFullYear())
const money = (v) => formatMoney(v)
// 概览卡按原项目的写法：不带千分位，保证金额不会因为太长而换行
const fixed = (v) => Number(v || 0).toFixed(2)

// 预算优先（实时数据），目标补充在后面；与原项目的"进度卡片"一致
const cards = computed(() => {
  const budgetCards = pickBudgets(budgets.value, 3).map((b) => ({
    id: `budget-${b.id}`, url: '/pages/budget/index', icon: '📊', title: b.name, typeLabel: '预算',
    percent: Math.min(Math.round(b.percentage), 100),
    color: b.isOverBudget ? '#FF7A6E' : '#8F78E6',
    left: `已用 ¥${money(b.spent)}`, right: `剩余 ¥${money(Math.max(0, b.remaining))}`,
  }))
  const goalCards = pickGoals(goals.value, 3).map((g) => ({
    id: `goal-${g.id}`, url: '/pages/goal/index', icon: g.icon || '🎯', title: g.name, typeLabel: '目标',
    percent: Math.round(g.progress), color: '#5CC9A0',
    left: `已存 ¥${money(g.currentAmount)}`, right: `目标 ¥${money(g.targetAmount)}`,
  }))
  return [...budgetCards, ...goalCards]
})

// 各块数据互不依赖：某一块失败（请求层会弹提示）不影响其他块显示
const safely = (promise, apply) => promise.then(apply).catch(() => {})

async function load() {
  await Promise.all([
    safely(billApi.statistics(monthRange()), (s) => { stats.value = s }),
    safely(billApi.list({ page: 1, limit: 5 }), (list) => { recent.value = list.items }),
    safely(budgetApi.progress(), (list) => { budgets.value = list }),
    safely(goalApi.list(), (list) => { goals.value = list }),
  ])
  loaded.value = true
  if (cardIndex.value >= cards.value.length) cardIndex.value = 0
}

onShow(load)
onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})

const go = (url) => uni.navigateTo({ url })
const goCreate = () => go('/pages/bills/create')
const goBills = (type) => go(`/pages/bills/index${type ? `?type=${type}` : ''}`)
const goDetail = (bill) => go(`/pages/bills/detail?id=${bill.id}`)
</script>

<style lang="scss" scoped>
.page {
  padding: calc(var(--status-bar-height) + 56rpx) 32rpx 0;
}
.header {
  margin-bottom: 48rpx;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.title {
  font-size: 58rpx;
  font-weight: 900;
}
.sticker {
  font-size: 40rpx;
  color: $ln-accent;
}
.year {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}

/* 概览卡 */
.overview {
  position: relative;
  padding: 40rpx;
  margin-bottom: 48rpx;
  color: #fff;
  background: $ln-primary;
  @include clay-box($ln-r-lg, 14rpx);
}
.tape {
  position: absolute;
  top: 24rpx;
  right: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  font-size: 40rpx;
  background: $ln-accent;
  transform: rotate(10deg);
  @include clay-box($ln-r-sm, 6rpx);
}
.ov-label {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
  color: rgba(255, 255, 255, 0.85);
}
.ov-balance {
  display: block;
  margin-top: 16rpx;
  font-size: 80rpx;
  font-weight: 900;
  letter-spacing: -3rpx;
  line-height: 1.15;
}
.ov-divider {
  height: $ln-bw-thin;
  margin: 32rpx 0;
  background: rgba(255, 255, 255, 0.3);
}
.ov-stats {
  display: flex;
  gap: 24rpx;
}
.stat {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx;
  background: rgba(255, 255, 255, 0.24);
  border-radius: $ln-r-md;
  box-shadow: inset 6rpx 6rpx 14rpx rgba(70, 40, 160, 0.25), inset -6rpx -6rpx 14rpx rgba(255, 255, 255, 0.3);
}
.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 64rpx;
  height: 64rpx;
  @include clay-box($ln-r-sm, 4rpx);
  &.expense-bg {
    background: $ln-error;
  }
  &.income-bg {
    background: $ln-success;
  }
}
.stat-label {
  display: block;
  font-size: 22rpx;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}
.stat-value {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  white-space: nowrap;
}

/* 进度卡片 */
.cards {
  margin-bottom: 16rpx;
}
.swiper {
  height: 290rpx;
}
.progress-card {
  height: 258rpx;
  margin: 0 14rpx 0 0;
  padding: 28rpx 32rpx;
  background: $ln-card;
  @include clay-box($ln-r-lg);
  @include clay-shadow(8rpx);
}
.pc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}
.pc-title {
  display: flex;
  align-items: center;
  gap: 20rpx;
}
.pc-icon {
  font-size: 44rpx;
}
.pc-name {
  display: block;
  font-size: 32rpx;
  font-weight: 800;
}
.pc-type {
  display: block;
  font-size: 22rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
.pc-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 20rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
.dots {
  display: flex;
  justify-content: center;
  gap: 12rpx;
  margin-top: 4rpx;
}
.dot {
  width: 16rpx;
  height: 16rpx;
  background: $ln-primary-light;
  border-radius: 50%;
  &.on {
    width: 36rpx;
    border-radius: 999rpx;
    background: $ln-primary;
  }
}
.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx;
  margin-bottom: 48rpx;
  background: $ln-card;
  border-radius: $ln-r-lg;
  @include clay-inset(8rpx);
}
.empty-icon {
  font-size: 64rpx;
  margin-bottom: 16rpx;
}
.empty-title {
  font-size: 28rpx;
  font-weight: 700;
  color: $ln-text-secondary;
}
.empty-hint {
  margin-top: 16rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-primary;
}

/* 近期交易 */
.section {
  margin-top: 40rpx;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32rpx;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.sticker-sm {
  font-size: 36rpx;
}
.st-text {
  font-size: 40rpx;
  font-weight: 800;
}
.all-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 24rpx;
  font-size: 26rpx;
  font-weight: 700;
  background: $ln-card;
  @include clay-box($ln-r-sm, $ln-bw-thin);
  @include clay-shadow(4rpx);
  @include clay-press(4rpx);
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
  padding: 48rpx;
  margin-right: 8rpx;
  background: $ln-card;
  @include clay-box($ln-r-lg);
  @include clay-shadow(8rpx);
}
</style>
