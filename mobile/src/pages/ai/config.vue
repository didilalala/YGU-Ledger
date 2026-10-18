<template>
  <view>
    <view v-for="c in configs" :key="c.id" class="card">
      <view class="head">
        <text class="name">{{ c.name }}</text>
        <text v-if="c.isDefault" class="tag">默认</text>
      </view>
      <text class="muted line">{{ providerName(c.provider) }} · {{ c.model }}</text>
      <text class="muted line">Key：{{ c.apiKeyMasked }}</text>
      <view class="ops">
        <text :class="{ busy: testing === c.id }" @click="test(c)">{{ testing === c.id ? '测试中…' : '测试连接' }}</text>
        <text v-if="!c.isDefault" @click="setDefault(c)">设为默认</text>
        <text @click="edit(c.id)">编辑</text>
        <text class="danger" @click="remove(c)">删除</text>
      </view>
    </view>
    <view v-if="loaded && !configs.length" class="card muted empty">
      还没有配置 AI 模型，点击下方按钮添加后即可使用 AI 记账
    </view>
    <view class="actions">
      <button class="primary" @click="edit()">添加模型</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { aiApi } from '@/api'
import { providerName } from './providers'

const configs = ref([])
const loaded = ref(false)
const testing = ref(null)

const load = async () => {
  configs.value = await aiApi.configs()
  loaded.value = true
}
onShow(load)

const edit = (id) => uni.navigateTo({ url: `/pages/ai/config-edit${id ? `?id=${id}` : ''}` })

async function test(c) {
  if (testing.value) return
  testing.value = c.id
  try {
    const { success, message } = await aiApi.testConfig(c.id)
    uni.showModal({ title: success ? '连接成功' : '连接失败', content: message, showCancel: false })
  } finally {
    testing.value = null
  }
}

async function setDefault(c) {
  await aiApi.setDefault(c.id)
  load()
}

async function remove(c) {
  const { confirm } = await uni.showModal({ title: '删除模型', content: `确定删除“${c.name}”吗？` })
  if (!confirm) return
  await aiApi.removeConfig(c.id)
  load()
}
</script>

<style lang="scss" scoped>
.head {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.name {
  font-size: 32rpx;
  font-weight: 600;
}
.tag {
  padding: 2rpx 14rpx;
  font-size: 22rpx;
  border-radius: 8rpx;
  color: $ln-primary;
  background: rgba(79, 110, 247, 0.12);
}
.line {
  display: block;
  margin-top: 8rpx;
}
.ops {
  display: flex;
  gap: 40rpx;
  margin-top: 24rpx;
  color: $ln-primary;
  .danger {
    color: $ln-expense;
  }
  .busy {
    color: $ln-text-secondary;
  }
}
.empty {
  text-align: center;
  padding: 48rpx 32rpx;
}
.actions {
  padding: 32rpx;
}
.primary {
  background: $ln-primary;
  color: #fff;
}
</style>
