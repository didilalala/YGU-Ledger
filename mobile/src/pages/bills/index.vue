<template>
  <view class="page">
    <ln-navbar title="全部账单" />

    <view class="filter-bar">
      <scroll-view scroll-x class="chips-scroll" :show-scrollbar="false">
        <view class="chips">
          <text v-for="(label, i) in typeLabels" :key="label" :class="['chip', { active: typeIndex === i }]"
            @click="onTypeChange(i)">{{ label }}</text>
          <view class="chip-sep" />
          <text v-for="p in presetChips" :key="p.key" :class="['chip', { active: activePreset === p.key }]"
            @click="applyPreset(p.key)">{{ p.label }}</text>
        </view>
      </scroll-view>

      <view class="range">
        <picker mode="date" :value="filter.startDate" :end="filter.endDate || undefined" @change="setDate('startDate', $event)">
          <view :class="['pick', { set: filter.startDate }]">{{ filter.startDate || '开始日期' }}</view>
        </picker>
        <text class="to">至</text>
        <picker mode="date" :value="filter.endDate" :start="filter.startDate || undefined" @change="setDate('endDate', $event)">
          <view :class="['pick', { set: filter.endDate }]">{{ filter.endDate || '结束日期' }}</view>
        </picker>
        <picker class="cat-picker" :range="categoryOptions" range-key="label" :value="categoryIndex" @change="setCategory">
          <view :class="['pick', { set: filter.categoryId }]">{{ categoryOptions[categoryIndex].label }}</view>
        </picker>
      </view>
    </view>

    <view v-if="summary" class="summary mono">
      共 {{ summary.count }} 笔
      <text v-if="typeIndex !== 2"> · 支出 <text class="expense">{{ formatMoney(summary.expense) }}</text></text>
      <text v-if="typeIndex !== 1"> · 收入 <text class="income">{{ formatMoney(summary.income) }}</text></text>
    </view>

    <view v-for="section in sections" :key="section.month" class="month">
      <view class="month-head">
        <text class="month-title">{{ monthLabel(section.month) }}</text>
        <text v-if="totals[section.month]" class="month-total mono">
          <text v-if="typeIndex !== 2" class="expense">支 {{ formatMoney(totals[section.month].expense) }}</text>
          <text v-if="typeIndex === 0">　</text>
          <text v-if="typeIndex !== 1" class="income">收 {{ formatMoney(totals[section.month].income) }}</text>
        </text>
      </view>
      <view class="list"><bill-item v-for="bill in section.items" :key="bill.id" :bill="bill" @click="goDetail" /></view>
    </view>

    <view v-if="loaded && !items.length" class="empty">
      <text class="empty-icon">📋</text>
      <text class="empty-text">暂无账单记录</text>
    </view>
    <text v-if="items.length" class="foot mono">{{ footText }}</text>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
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

const presetChips = DATE_PRESETS.filter((p) => p.key !== 'all')
const sections = computed(() => groupByMonth(items.value))
const footText = computed(() => (loading.value ? '加载中…' : hasNext.value ? '上拉加载更多' : '没有更多了'))
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

function onTypeChange(index) {
  if (index === typeIndex.value) return
  typeIndex.value = index
  // 当前选中的分类不属于新类型时清掉，否则会筛出空列表
  if (!categoryOptions.value.some((o) => o.id === filter.categoryId)) filter.categoryId = null
  refresh()
}

// 再点一次已选中的快捷项，回到不限日期
function applyPreset(key) {
  const { startDate = '', endDate = '' } = presetRange(activePreset.value === key ? 'all' : key)
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

// 首页的"总支出 / 总收入"会带着类型进来
onLoad((query) => {
  const index = TYPES.indexOf(query.type)
  if (index > 0) typeIndex.value = index
})

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
.filter-bar {
  padding: 24rpx 32rpx;
  background: $ln-card;
  border-bottom: $ln-bw-thin solid $ln-stroke;
}
.chips-scroll {
  white-space: nowrap;
}
.chips {
  display: inline-flex;
  align-items: center;
  gap: 16rpx;
}
.chip {
  flex-shrink: 0;
  white-space: nowrap;
  padding: 12rpx 32rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: $ln-text-secondary;
  background: $ln-card;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
  &.active {
    color: #fff;
    font-weight: 800;
    background: $ln-primary;
  }
}
.chip-sep {
  width: $ln-bw-thin;
  height: 40rpx;
  margin: 0 8rpx;
  background: $ln-border;
}
.range {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 20rpx;
}
.pick {
  padding: 8rpx 20rpx;
  font-size: 24rpx;
  font-weight: 700;
  color: $ln-text-secondary;
  background: $ln-bg;
  border: $ln-bw-thin solid $ln-border;
  border-radius: $ln-r-sm;
  &.set {
    color: $ln-text;
    border-color: $ln-stroke;
  }
}
.to {
  font-size: 24rpx;
  color: $ln-text-secondary;
}
.cat-picker {
  margin-left: auto;
}
.summary {
  padding: 24rpx 32rpx 0;
  font-size: 24rpx;
  font-weight: 700;
  color: $ln-text-secondary;
}
.month {
  margin-top: 24rpx;
}
.month-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 32rpx;
  background: $ln-card;
  border-top: $ln-bw-thin solid $ln-stroke;
  border-bottom: $ln-bw-thin solid $ln-stroke;
}
.month-title {
  font-size: 30rpx;
  font-weight: 800;
}
.month-total {
  font-size: 26rpx;
  font-weight: 800;
}
.list {
  padding: 28rpx 32rpx 0;
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 200rpx;
}
.empty-icon {
  margin-bottom: 24rpx;
  font-size: 96rpx;
}
.empty-text {
  font-size: 30rpx;
  font-weight: 700;
  color: $ln-text-secondary;
}
.foot {
  display: block;
  padding: 16rpx 0 64rpx;
  text-align: center;
  font-size: 24rpx;
  color: $ln-text-secondary;
}
</style>
