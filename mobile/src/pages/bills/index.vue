<template>
  <view>
    <view class="filter">
      <uni-segmented-control :current="typeIndex" :values="typeLabels" style-type="text" @clickItem="onTypeChange" />
    </view>

    <view class="card list">
      <bill-item v-for="bill in items" :key="bill.id" :bill="bill" @click="goDetail" />
      <uni-load-more :status="loadStatus" />
    </view>

    <!-- TODO: 按日期区间筛选、按月分组与月度小计（对应原项目 AllBillsScreen） -->
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { billApi } from '@/api'

const TYPES = [undefined, 'expense', 'income']
const typeLabels = ['全部', '支出', '收入']
const typeIndex = ref(0)

const items = ref([])
const page = ref(1)
const hasNext = ref(true)
const loading = ref(false)

const loadStatus = computed(() => (loading.value ? 'loading' : hasNext.value ? 'more' : 'noMore'))

async function load(reset = false) {
  if (loading.value || (!reset && !hasNext.value)) return
  loading.value = true
  try {
    const nextPage = reset ? 1 : page.value
    const data = await billApi.list({ page: nextPage, limit: 20, type: TYPES[typeIndex.value] })
    items.value = reset ? data.items : items.value.concat(data.items)
    hasNext.value = data.pagination.hasNext
    page.value = nextPage + 1
  } finally {
    loading.value = false
  }
}

function onTypeChange(e) {
  typeIndex.value = e.currentIndex
  load(true)
}

onShow(() => load(true).catch(() => {}))
onReachBottom(() => load().catch(() => {}))
onPullDownRefresh(async () => {
  await load(true).catch(() => {})
  uni.stopPullDownRefresh()
})

const goDetail = (bill) => uni.navigateTo({ url: `/pages/bills/detail?id=${bill.id}` })
</script>

<style lang="scss" scoped>
.filter {
  background: $ln-card;
  padding: 16rpx 32rpx;
}
.list {
  padding-top: 8rpx;
}
</style>
