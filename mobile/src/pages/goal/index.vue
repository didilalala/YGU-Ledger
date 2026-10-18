<template>
  <view>
    <view v-for="g in goals" :key="g.id" class="card">
      <view class="row">
        <text class="name">{{ g.icon || '🎯' }} {{ g.name }}</text>
        <text class="muted">{{ g.deadline ? `截止 ${g.deadline}` : '' }}</text>
      </view>
      <progress :percent="g.progress" activeColor="#16a34a" stroke-width="6" show-info />
      <text class="muted">{{ formatMoney(g.currentAmount) }} / {{ formatMoney(g.targetAmount) }}</text>
    </view>
    <view v-if="!goals.length" class="card muted empty">还没有财务目标</view>
    <!-- TODO: 新建/编辑目标、存入金额 -->
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { goalApi } from '@/api'
import { formatMoney } from '@/utils/format'

const goals = ref([])

onShow(async () => {
  goals.value = await goalApi.list()
})
</script>

<style lang="scss" scoped>
.row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16rpx;
}
.name {
  font-weight: 600;
}
.empty {
  text-align: center;
}
</style>
