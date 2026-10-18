<template>
  <view class="page">
    <ln-navbar :title="id ? '编辑模型配置' : '添加模型配置'" />

    <view class="form">
      <view class="form-field">
        <text class="label">服务商</text>
        <view class="providers">
          <view v-for="p in PROVIDERS" :key="p.value" :class="['provider', { selected: form.provider === p.value }]" @click="onProvider(p)">
            <image class="p-logo" :src="p.logo" mode="aspectFit" />
            <text class="p-name">{{ p.label }}</text>
          </view>
        </view>
      </view>
      <view class="form-field">
        <text class="label">名称</text>
        <input v-model="form.name" placeholder="如：我的 Claude" />
      </view>
      <view class="form-field">
        <text class="label">API Key</text>
        <input v-model="form.apiKey" password :placeholder="id ? `${masked}（不修改请留空）` : '请输入 API Key'" />
      </view>
      <view class="form-field">
        <text class="label">API 地址（可选）</text>
        <input v-model="form.apiBaseUrl" placeholder="留空使用官方地址（需含 /v1 等路径）" />
      </view>
      <view class="form-field">
        <text class="label">模型</text>
        <input v-model="form.model" placeholder="模型名称" />
      </view>
      <view class="form-field row">
        <view>
          <text class="label">支持图片识别</text>
          <text class="hint">此服务商支持图片</text>
        </view>
        <switch :checked="form.supportsVision" color="#3B82F6" @change="form.supportsVision = $event.detail.value" />
      </view>
    </view>

    <view class="bottom-actions">
      <view class="btn" @click="back">取消</view>
      <view :class="['btn btn-primary', { disabled: saving }]" @click="save">{{ saving ? '保存中…' : '保存' }}</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { aiApi } from '@/api'
import { PROVIDERS } from './providers'

const id = ref(null)
const masked = ref('')
const saving = ref(false)
const form = reactive({
  provider: PROVIDERS[0].value,
  name: '',
  model: PROVIDERS[0].model,
  apiKey: '',
  apiBaseUrl: '',
  supportsVision: PROVIDERS[0].vision,
})

function onProvider(p) {
  // 名称、模型还是预设值时才跟着换，用户改过的不覆盖
  const old = PROVIDERS.find((x) => x.value === form.provider)
  if (!form.model || form.model === old.model) form.model = p.model
  if (!form.name || form.name === old.label) form.name = p.label
  form.provider = p.value
  form.supportsVision = p.vision
}

onLoad(async (query) => {
  if (!query.id) {
    form.name = PROVIDERS[0].label
    return
  }
  id.value = Number(query.id)
  const c = (await aiApi.configs()).find((x) => x.id === id.value)
  if (!c) return uni.navigateBack()
  masked.value = c.apiKeyMasked
  Object.assign(form, {
    provider: c.provider, name: c.name, model: c.model,
    apiBaseUrl: c.apiBaseUrl || '', supportsVision: c.supportsVision,
  })
})

const back = () => uni.navigateBack()

async function save() {
  if (saving.value) return
  const data = {
    provider: form.provider,
    name: form.name.trim(),
    model: form.model.trim(),
    apiBaseUrl: form.apiBaseUrl.trim() || null,
    supportsVision: form.supportsVision,
  }
  if (!data.name || !data.model) return uni.showToast({ title: '请填写名称和模型', icon: 'none' })
  const key = form.apiKey.trim()
  if (key) data.apiKey = key
  else if (!id.value) return uni.showToast({ title: '请填写 API Key', icon: 'none' })

  saving.value = true
  try {
    if (id.value) await aiApi.updateConfig(id.value, data)
    else await aiApi.createConfig(data)
    uni.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 500)
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.page {
  padding-bottom: calc(200rpx + env(safe-area-inset-bottom));
}
.providers {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.provider {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx 24rpx;
  background: $ln-card;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
  &.selected {
    background: $ln-accent;
    border-width: $ln-bw;
  }
}
.p-logo {
  width: 44rpx;
  height: 44rpx;
}
.p-name {
  font-size: 28rpx;
  font-weight: 800;
}
.bottom-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  display: flex;
  gap: 24rpx;
  padding: 24rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
  background: $ln-bg;
  border-top: $ln-bw-thin solid $ln-stroke;
  .btn {
    flex: 1;
    &.disabled {
      opacity: 0.6;
    }
  }
}
</style>
