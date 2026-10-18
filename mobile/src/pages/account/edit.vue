<template>
  <view class="page">
    <ln-navbar :title="id ? '编辑账户' : '添加账户'" />
    <view class="form">
      <view class="form-field">
        <text class="label">名称</text>
        <input v-model="form.name" placeholder="如：工商银行储蓄卡" maxlength="30" />
      </view>
      <view class="form-field">
        <text class="label">类型</text>
        <picker :range="ACCOUNT_TYPES" range-key="label" :value="typeIndex" @change="onType">
          <view class="value">{{ ACCOUNT_TYPES[typeIndex].label }} ›</view>
        </picker>
      </view>
      <view class="form-field">
        <text class="label">{{ form.type === 'credit_card' ? '欠款金额' : '当前余额' }}</text>
        <input v-model="form.balance" type="text" placeholder="0.00" />
      </view>
      <view class="form-field">
        <text class="label">图标</text>
        <input v-model="form.icon" :placeholder="ACCOUNT_TYPES[typeIndex].icon" maxlength="4" />
      </view>
      <view class="form-field row">
        <text class="label">设为默认账户</text>
        <switch :checked="form.isDefault" color="#4f6ef7" @change="form.isDefault = $event.detail.value" />
      </view>
    </view>
    <view class="muted tip">
      余额需要手动维护，不会随账单自动变化。信用卡请填写欠款金额（填正数或负数均按负债计算）。
    </view>
    <view class="form-actions">
      <button class="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
      <button v-if="id" class="danger" @click="remove">删除账户</button>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { accountApi } from '@/api'
import { parseAmount } from '@/utils/format'
import { ACCOUNT_TYPES } from './types'

const id = ref(null)
const saving = ref(false)
const form = reactive({ name: '', type: 'bank_card', balance: '0', icon: '', isDefault: false })
const typeIndex = computed(() => Math.max(0, ACCOUNT_TYPES.findIndex((t) => t.value === form.type)))

const onType = (e) => { form.type = ACCOUNT_TYPES[e.detail.value].value }

onLoad(async (query) => {
  if (!query.id) return
  id.value = Number(query.id)
  const a = (await accountApi.list()).find((x) => x.id === id.value)
  if (!a) return uni.navigateBack()
  Object.assign(form, { name: a.name, type: a.type, balance: String(a.balance), icon: a.icon || '', isDefault: a.isDefault })
})

async function save() {
  const balance = parseAmount(form.balance)
  if (!form.name.trim()) return uni.showToast({ title: '请填写账户名称', icon: 'none' })
  if (Number.isNaN(balance)) return uni.showToast({ title: '请输入正确的金额', icon: 'none' })
  const data = { name: form.name.trim(), type: form.type, balance, icon: form.icon.trim() || null, isDefault: form.isDefault }
  saving.value = true
  try {
    if (id.value) await accountApi.update(id.value, data)
    else await accountApi.create(data)
    uni.navigateBack()
  } finally {
    saving.value = false
  }
}

async function remove() {
  const { confirm } = await uni.showModal({
    title: '删除账户',
    content: '关联到该账户的账单会保留，只是不再属于任何账户。确定删除吗？',
  })
  if (!confirm) return
  await accountApi.remove(id.value)
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.tip {
  padding: 0 32rpx;
  line-height: 1.6;
}
</style>
