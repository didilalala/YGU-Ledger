<template>
 <view>
  <view class="form card">
    <view class="field">
      <text class="label">服务商</text>
      <picker :range="PROVIDERS" range-key="label" :value="providerIndex" @change="onProvider">
        <view class="value">{{ PROVIDERS[providerIndex].label }} ›</view>
      </picker>
    </view>
    <view class="field">
      <text class="label">名称</text>
      <input v-model="form.name" placeholder="如：我的 DeepSeek" />
    </view>
    <view class="field">
      <text class="label">模型</text>
      <input v-model="form.model" placeholder="模型名称" />
    </view>
    <view class="field">
      <text class="label">API Key</text>
      <input v-model="form.apiKey" password :placeholder="id ? `${masked}（不修改请留空）` : '粘贴你的 API Key'" />
    </view>
    <view class="field">
      <text class="label">API 地址</text>
      <input v-model="form.apiBaseUrl" placeholder="可选，留空使用官方地址（需含 /v1 等路径）" />
    </view>
    <view class="field">
      <text class="label">支持图片识别</text>
      <switch :checked="form.supportsVision" color="#4f6ef7" @change="form.supportsVision = $event.detail.value" />
    </view>
  </view>
  <view class="actions">
    <button class="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
  </view>
 </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
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
const providerIndex = computed(() => Math.max(0, PROVIDERS.findIndex((p) => p.value === form.provider)))

function onProvider(e) {
  const p = PROVIDERS[e.detail.value]
  // 名称、模型还是预设值时才跟着换，用户改过的不覆盖
  const old = PROVIDERS[providerIndex.value]
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
  uni.setNavigationBarTitle({ title: '编辑模型' })
  const c = (await aiApi.configs()).find((x) => x.id === id.value)
  if (!c) return uni.navigateBack()
  masked.value = c.apiKeyMasked
  Object.assign(form, {
    provider: c.provider, name: c.name, model: c.model,
    apiBaseUrl: c.apiBaseUrl || '', supportsVision: c.supportsVision,
  })
})

async function save() {
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
.field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid $ln-border;
  &:last-child {
    border-bottom: none;
  }
  input {
    flex: 1;
    text-align: right;
  }
}
.label {
  flex-shrink: 0;
}
.value {
  color: $ln-primary;
}
.actions {
  padding: 32rpx;
}
.primary {
  background: $ln-primary;
  color: #fff;
}
</style>
