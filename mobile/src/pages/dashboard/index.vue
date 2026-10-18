<template>
  <view class="page">
    <view class="card summary">
      <text class="muted">本月结余</text>
      <text class="balance">{{ formatMoney(stats.balance) }}</text>
      <view class="row">
        <view class="col">
          <text class="muted">收入</text>
          <text class="income">{{ formatMoney(stats.totalIncome) }}</text>
        </view>
        <view class="col">
          <text class="muted">支出</text>
          <text class="expense">{{ formatMoney(stats.totalExpense) }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>最近账单</text>
        <text class="muted" @click="goBills">全部 ›</text>
      </view>
      <bill-item v-for="bill in recent" :key="bill.id" :bill="bill" @click="goDetail" />
      <view v-if="!recent.length" class="muted empty">还没有账单，点击右下角记一笔</view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>本期预算</text>
        <text class="muted" @click="go('/pages/budget/index')">{{ budgets.length ? '全部 ›' : '' }}</text>
      </view>
      <view v-for="b in shownBudgets" :key="b.id" class="item">
        <view class="item-head">
          <text>{{ budgetLabel(b) }} · {{ b.name }}</text>
          <text :class="b.isOverBudget ? 'expense' : 'muted'">{{ b.isOverBudget ? '已超支' : b.isAlert ? '接近上限' : '' }}</text>
        </view>
        <progress :percent="Math.min(b.percentage, 100)" :activeColor="b.isAlert ? '#e5484d' : '#4f6ef7'" stroke-width="6" />
        <text class="muted">已用 {{ formatMoney(b.spent) }} / {{ formatMoney(b.amount) }}</text>
      </view>
      <view v-if="!budgets.length" class="muted empty" @click="go('/pages/budget/edit')">还没有预算，去设置一个 ›</view>
    </view>

    <view class="card">
      <view class="section-title">
        <text>财务目标</text>
        <text class="muted" @click="go('/pages/goal/index')">{{ goals.length ? '全部 ›' : '' }}</text>
      </view>
      <view v-for="g in shownGoals" :key="g.id" class="item">
        <view class="item-head">
          <text>{{ g.icon || '🎯' }} {{ g.name }}</text>
          <text :class="isOverdue(g.deadline) ? 'expense' : 'muted'">{{ deadlineText(g.deadline) }}</text>
        </view>
        <progress :percent="g.progress" activeColor="#16a34a" stroke-width="6" show-info />
        <text class="muted">{{ formatMoney(g.currentAmount) }} / {{ formatMoney(g.targetAmount) }}</text>
      </view>
      <view v-if="goals.length && !shownGoals.length" class="muted empty">目标都完成了 🎉</view>
      <view v-if="!goals.length" class="muted empty" @click="go('/pages/goal/edit')">还没有目标，去设置一个 ›</view>
    </view>

    <view class="card shortcuts">
      <view v-for="s in SHORTCUTS" :key="s.label" class="shortcut" @click="s.action()">
        <text class="shortcut-icon">{{ s.icon }}</text>
        <text class="muted">{{ s.label }}</text>
      </view>
    </view>

    <view class="fab" @click="goCreate">＋</view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { billApi, budgetApi, goalApi } from '@/api'
import { useCategoryStore } from '@/stores/category'
import { daysLeft, deadlineText, pickBudgets, pickGoals } from '@/utils/dashboard'
import { formatMoney, monthRange } from '@/utils/format'

const categoryStore = useCategoryStore()
const stats = ref({ balance: 0, totalIncome: 0, totalExpense: 0 })
const recent = ref([])
const budgets = ref([])
const goals = ref([])

const shownBudgets = computed(() => pickBudgets(budgets.value))
const shownGoals = computed(() => pickGoals(goals.value))

const budgetLabel = (b) => {
  const c = b.categoryId && categoryStore.list.find((x) => x.id === b.categoryId)
  return c ? `${c.icon || ''}${c.name}` : '总预算'
}
const isOverdue = (deadline) => daysLeft(deadline) < 0

// 各块数据互不依赖：某一块失败（请求层会弹提示）不影响其他块显示
const safely = (promise, apply) => promise.then(apply).catch(() => {})

function load() {
  return Promise.all([
    safely(billApi.statistics(monthRange()), (s) => { stats.value = s }),
    safely(billApi.list({ page: 1, limit: 5 }), (list) => { recent.value = list.items }),
    safely(budgetApi.progress(), (list) => { budgets.value = list }),
    safely(goalApi.list(), (list) => { goals.value = list }),
    categoryStore.load().catch(() => {}),
  ])
}

// 从记账页返回时刷新
onShow(load)

const go = (url) => uni.navigateTo({ url })
const SHORTCUTS = [
  { icon: '✏️', label: '记一笔', action: () => go('/pages/bills/create') },
  { icon: '🤖', label: 'AI 记账', action: () => uni.switchTab({ url: '/pages/ai/chat' }) },
  { icon: '💰', label: '预算', action: () => go('/pages/budget/index') },
  { icon: '🎯', label: '目标', action: () => go('/pages/goal/index') },
  { icon: '🗂️', label: '分类', action: () => go('/pages/category/index') },
]

const goCreate = () => uni.navigateTo({ url: '/pages/bills/create' })
const goBills = () => uni.switchTab({ url: '/pages/bills/index' })
const goDetail = (bill) => uni.navigateTo({ url: `/pages/bills/detail?id=${bill.id}` })
</script>

<style lang="scss" scoped>
.page {
  padding-bottom: 200rpx; /* 避免最后一张卡片被右下角的悬浮按钮遮住 */
}
.summary {
  background: $ln-primary;
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  .muted,
  .income,
  .expense {
    color: rgba(255, 255, 255, 0.85);
  }
}
.balance {
  font-size: 64rpx;
  font-weight: 700;
}
.row {
  display: flex;
  margin-top: 16rpx;
}
.col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.section-title {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
  margin-bottom: 8rpx;
}
.empty {
  padding: 48rpx 0;
  text-align: center;
}
.item {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  padding: 12rpx 0 16rpx;
}
.item-head {
  display: flex;
  justify-content: space-between;
}
.shortcuts {
  display: flex;
  justify-content: space-around;
}
.shortcut {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}
.shortcut-icon {
  font-size: 48rpx;
}
.fab {
  position: fixed;
  right: 48rpx;
  bottom: calc(48rpx + var(--window-bottom));
  width: 112rpx;
  height: 112rpx;
  border-radius: 50%;
  background: $ln-primary;
  color: #fff;
  font-size: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(79, 110, 247, 0.4);
}
</style>
