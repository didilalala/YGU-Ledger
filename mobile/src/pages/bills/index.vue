<template>
  <view>
    <view class="filter">
      <uni-segmented-control :current="typeIndex" :values="typeLabels" style-type="text" @clickItem="onTypeChange" />

      <view class="chips">
        <text v-for="p in DATE_PRESETS" :key="p.key" :class="['chip', { on: activePreset === p.key }]"
          @click="applyPreset(p.key)">{{ p.label }}</text>
      </view>

      <view class="range">
        <picker mode="date" :value="filter.startDate" :end="filter.endDate || undefined" @change="setDate('startDate', $event)">
          <text class="value">{{ filter.startDate || '开始日期' }}</text>
        </picker>
        <text class="muted">至</text>
        <picker mode="date" :value="filter.endDate" :start="filter.startDate || undefined" @change="setDate('endDate', $event)">
          <text class="value">{{ filter.endDate || '结束日期' }}</text>
        </picker>
        <picker class="category-picker" :range="categoryOptions" range-key="label" :value="categoryIndex" @change="setCategory">
          <text class="value">{{ categoryOptions[categoryIndex].label }} ›</text>
        </picker>
      </view>
    </view>

    <view v-if="summary" class="summary muted">
      共 {{ summary.count }} 笔
      <text v-if="typeIndex !== 2"> · 支出 <text class="expense">{{ formatMoney(summary.expense) }}</text></text>
      <text v-if="typeIndex !== 1"> · 收入 <text class="income">{{ formatMoney(summary.income) }}</text></text>
    </view>

    <view v-for="section in sections" :key="section.month" class="card list">
      <view class="month-head">
        <text class="month">{{ monthLabel(section.month) }}</text>
        <text v-if="totals[section.month]" class="muted">
          <text v-if="typeIndex !== 2">支出 {{ formatMoney(totals[section.month].expense) }}</text>
          <text v-if="typeIndex === 0">　</text>
          <text v-if="typeIndex !== 1">收入 {{ formatMoney(totals[section.month].income) }}</text>
        </text>
      </view>
      <bill-item v-for="bill in section.items" :key="bill.id" :bill="bill" @click="goDetail" />
    </view>

    <view v-if="loaded && !items.length" class="card muted empty">没有符合条件的账单</view>
    <uni-load-more v-if="items.length" :status="loadStatus" />
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { billApi } from '@/api'
import { useCategoryStore } from '@/stores/category'
import { formatMoney } from '@/utils/format'
import { DATE_PRESETS, groupByMonth, matchPreset, monthLabel, monthlyTotals, presetRange } from '@/utils/bill-filter'

const TYPES = [undefined, 'expense', 'income']
const typeLabels = ['全部', '支出', '收入']
const typeIndex = ref(0)
const filter = reactive({ startDate: '', endDate: '', categoryId: null })

const categoryStore = useCategoryStore()

const items = ref([])
const page = ref(1)
const hasNext = ref(true)
const loading = ref(false)
const loaded = ref(false)
const totals = ref({}) // 月份 → { income, expense }，来自服务端，不受分页影响
const summary = ref(null)

const sections = computed(() => groupByMonth(items.value))
const loadStatus = computed(() => (loading.value ? 'loading' : hasNext.value ? 'more' : 'noMore'))
const activePreset = computed(() => matchPreset(filter.startDate, filter.endDate))

// 选了收入 / 支出时，分类只列对应类型；"全部"时列出所有
const categoryOptions = computed(() => {
  const type = TYPES[typeIndex.value]
  const list = type ? categoryStore.list.filter((c) => c.type === type) : categoryStore.list
  return [{ id: null, label: '全部分类' },
    ...list.map((c) => ({ id: c.id, label: `${c.icon || ''}${c.name}${type ? '' : c.type === 'income' ? '（收入）' : ''}` }))]
})
const categoryIndex = computed(() => Math.max(0, categoryOptions.value.findIndex((o) => o.id === filter.categoryId)))

const query = () => ({
  type: TYPES[typeIndex.value],
  categoryId: filter.categoryId || undefined,
  startDate: filter.startDate || undefined,
  endDate: filter.endDate || undefined,
})

// 筛选条件连续变化时，旧请求可能晚于新请求返回；用序号丢弃过期的响应
let listSeq = 0
let statsSeq = 0

async function load(reset = false) {
  if (!reset && (loading.value || !hasNext.value)) return
  const seq = reset ? ++listSeq : listSeq
  loading.value = true
  try {
    const nextPage = reset ? 1 : page.value
    const data = await billApi.list({ page: nextPage, limit: 20, ...query() })
    if (seq !== listSeq) return
    items.value = reset ? data.items : items.value.concat(data.items)
    hasNext.value = data.pagination.hasNext
    page.value = nextPage + 1
  } finally {
    if (seq === listSeq) {
      loading.value = false
      loaded.value = true
    }
  }
}

/** 月度小计与总计走统计接口：分页只加载了一部分账单，在前端累加会不准 */
async function loadStats() {
  const seq = ++statsSeq
  const { type, ...rest } = query() // 统计接口同时返回收入和支出，类型在显示时再取舍
  const stats = await billApi.statistics({ ...rest, granularity: 'monthly' })
  if (seq !== statsSeq) return
  totals.value = monthlyTotals(stats.trend)
  const count = type === 'expense' ? stats.expenseCount : type === 'income' ? stats.incomeCount
    : stats.expenseCount + stats.incomeCount
  summary.value = { count, income: stats.totalIncome, expense: stats.totalExpense }
}

const refresh = () => Promise.all([load(true), loadStats()]).catch(() => {})

function onTypeChange(e) {
  typeIndex.value = e.currentIndex
  // 当前选中的分类不属于新类型时清掉，否则会筛出空列表
  if (!categoryOptions.value.some((o) => o.id === filter.categoryId)) filter.categoryId = null
  refresh()
}

function applyPreset(key) {
  const { startDate = '', endDate = '' } = presetRange(key)
  Object.assign(filter, { startDate, endDate })
  refresh()
}

function setDate(field, e) {
  filter[field] = e.detail.value
  refresh()
}

function setCategory(e) {
  filter.categoryId = categoryOptions.value[e.detail.value].id
  refresh()
}

onShow(() => {
  categoryStore.load().catch(() => {})
  refresh()
})
onReachBottom(() => load().catch(() => {}))
onPullDownRefresh(async () => {
  await refresh()
  uni.stopPullDownRefresh()
})

const goDetail = (bill) => uni.navigateTo({ url: `/pages/bills/detail?id=${bill.id}` })
</script>

<style lang="scss" scoped>
.filter {
  background: $ln-card;
  padding: 16rpx 32rpx 24rpx;
}
.chips {
  display: flex;
  gap: 16rpx;
  margin-top: 16rpx;
}
.chip {
  padding: 6rpx 24rpx;
  border-radius: 28rpx;
  background: $ln-bg;
  font-size: 26rpx;
  &.on {
    background: rgba(79, 110, 247, 0.15);
    color: $ln-primary;
  }
}
.range {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 20rpx;
  font-size: 26rpx;
}
.value {
  color: $ln-primary;
}
.category-picker {
  margin-left: auto;
}
.summary {
  padding: 16rpx 32rpx 0;
}
.list {
  padding-top: 8rpx;
}
.month-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 16rpx 0 8rpx;
  border-bottom: 1rpx solid $ln-border;
}
.month {
  font-weight: 600;
}
.empty {
  text-align: center;
}
</style>
