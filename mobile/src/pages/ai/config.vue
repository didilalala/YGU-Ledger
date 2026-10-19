<template>
  <view class="page">
    <ln-navbar title="AI 模型配置" />

    <view class="panel">
      <view class="panel-head"><text class="panel-icon">🤖</text><text class="panel-title">AI 模型配置</text></view>

      <view v-for="c in configs" :key="c.id" class="cfg">
        <view class="cfg-head">
          <image v-if="providerLogo(c.provider)" class="logo" :src="providerLogo(c.provider)" mode="aspectFit" />
          <text class="cfg-name">{{ c.name }}</text>
          <text v-if="c.isDefault" class="default-tag">默认</text>
        </view>
        <text class="cfg-model">{{ c.model }}</text>
        <text class="cfg-key mono">Key：{{ c.apiKeyMasked }}</text>
        <view class="ops">
          <view v-if="!c.isDefault" class="op blue" @click="setDefault(c)"><text>设为默认</text></view>
          <view :class="['op blue', { busy: testing === c.id }]" @click="test(c)"><text>{{ testing === c.id ? '测试中…' : '测试' }}</text></view>
          <view class="op blue" @click="edit(c.id)"><text>编辑</text></view>
          <view class="op red" @click="remove(c)"><text>删除</text></view>
        </view>
      </view>

      <view v-if="loaded && !configs.length" class="empty-tip">还没有配置 AI 模型，添加后即可使用 AI 记账</view>

      <view class="add-btn" @click="edit()"><ln-icon name="plus" :size="36" :stroke="3" /><text>添加模型配置</text></view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { aiApi } from '@/api'
import { providerLogo } from './providers'

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
.panel {
  padding: 32rpx;
  margin: 32rpx;
  background: $ln-card;
  @include clay-box($ln-r-lg);
}
.panel-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 28rpx;
}
.panel-icon {
  font-size: 44rpx;
}
.panel-title {
  font-size: 38rpx;
  font-weight: 800;
}
.cfg {
  padding: 28rpx;
  margin-bottom: 24rpx;
  background: $ln-bg;
  border-radius: $ln-r-md;
  @include clay-inset(6rpx);
}
.cfg-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.logo {
  width: 48rpx;
  height: 48rpx;
}
.cfg-name {
  font-size: 36rpx;
  font-weight: 800;
}
.default-tag {
  font-size: 24rpx;
  font-weight: 800;
  color: $ln-primary;
}
.cfg-model {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 500;
  color: $ln-text-secondary;
}
.cfg-key {
  display: block;
  margin-top: 4rpx;
  font-size: 24rpx;
  color: $ln-text-secondary;
}
.ops {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 24rpx;
}
.op {
  padding: 8rpx 24rpx;
  font-size: 28rpx;
  font-weight: 800;
  background: $ln-card;
  @include clay-box($ln-r-sm, 4rpx);
  @include clay-press(4rpx);
  &.blue {
    color: $ln-primary;
  }
  &.red {
    color: $ln-error;
  }
  &.busy {
    opacity: 0.5;
  }
}
.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  min-height: 104rpx;
  margin-top: 8rpx;
  font-size: 32rpx;
  font-weight: 800;
  background: $ln-accent;
  @include clay-box($ln-r-md, 8rpx);
  @include clay-press(8rpx);
}
</style>
