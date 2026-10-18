<template>
  <view>
    <view v-for="g in goals" :key="g.id" class="card" @click="edit(g.id)">
      <view class="row">
        <text class="name">{{ g.icon || '🎯' }} {{ g.name }}</text>
        <text v-if="g.isCompleted" class="income">已完成 ✓</text>
        <text v-else class="muted">{{ g.deadline ? `截止 ${g.deadline}` : '' }}</text>
      </view>
      <progress :percent="g.progress" activeColor="#16a34a" stroke-width="6" show-info />
      <text class="muted">{{ formatMoney(g.currentAmount) }} / {{ formatMoney(g.targetAmount) }}</text>
    </view>
    <view v-if="loaded && !goals.length" class="card muted empty">还没有财务目标</view>
    <view class="form-actions">
      <button class="primary" @click="edit()">新建目标</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { goalApi } from '@/api'
import { formatMoney } from '@/utils/format'

const goals = ref([])
const loaded = ref(false)

onShow(async () => {
  goals.value = await goalApi.list()
  loaded.value = true
})

const edit = (id) => uni.navigateTo({ url: `/pages/goal/edit${id ? `?id=${id}` : ''}` })
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
