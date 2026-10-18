<template>
  <view>
    <view class="card">
      <view class="form-field">
        <text class="label">名称</text>
        <input v-model="form.name" placeholder="如：餐饮预算" />
      </view>
      <view class="form-field">
        <text class="label">金额</text>
        <input v-model="form.amount" type="digit" placeholder="预算金额" />
      </view>
      <view class="form-field">
        <text class="label">周期</text>
        <picker :range="PERIODS" range-key="label" :value="periodIndex" @change="form.period = PERIODS[$event.detail.value].value">
          <view class="value">{{ PERIODS[periodIndex].label }} ›</view>
        </picker>
      </view>
      <view class="form-field">
        <text class="label">范围</text>
        <picker :range="scopes" range-key="label" :value="scopeIndex" @change="form.categoryId = scopes[$event.detail.value].id">
          <view class="value">{{ scopes[scopeIndex].label }} ›</view>
        </picker>
      </view>
      <view class="form-field">
        <text class="label">超过多少 % 时提醒</text>
        <input v-model="form.alertAt" type="number" placeholder="1-100" />
      </view>
      <view class="form-field">
        <text class="label">启用</text>
        <switch :checked="form.isActive" color="#4f6ef7" @change="form.isActive = $event.detail.value" />
      </view>
    </view>
    <view class="form-actions">
      <button class="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
      <button v-if="id" class="danger" @click="remove">删除预算</button>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { budgetApi } from '@/api'
import { useCategoryStore } from '@/stores/category'

const PERIODS = [
  { value: 'monthly', label: '每月' },
  { value: 'yearly', label: '每年' },
]

const categoryStore = useCategoryStore()
const id = ref(null)
const saving = ref(false)
const form = reactive({ name: '', amount: '', period: 'monthly', categoryId: null, alertAt: '80', isActive: true })

// 预算只统计支出，所以范围里只列支出分类；null 表示总预算
const scopes = computed(() => [{ id: null, label: '全部支出（总预算）' },
  ...categoryStore.expense.map((c) => ({ id: c.id, label: `${c.icon || ''}${c.name}` }))])
const scopeIndex = computed(() => Math.max(0, scopes.value.findIndex((s) => s.id === form.categoryId)))
const periodIndex = computed(() => PERIODS.findIndex((p) => p.value === form.period))

onLoad(async (query) => {
  await categoryStore.load()
  if (!query.id) return
  id.value = Number(query.id)
  uni.setNavigationBarTitle({ title: '编辑预算' })
  const b = (await budgetApi.list()).find((x) => x.id === id.value)
  if (!b) return uni.navigateBack()
  Object.assign(form, { name: b.name, amount: String(b.amount), period: b.period,
    categoryId: b.categoryId, alertAt: String(b.alertAt), isActive: b.isActive })
})

async function save() {
  const amount = Number(form.amount)
  const alertAt = Number(form.alertAt)
  if (!form.name.trim()) return uni.showToast({ title: '请填写名称', icon: 'none' })
  if (!(amount > 0)) return uni.showToast({ title: '请填写大于 0 的金额', icon: 'none' })
  if (!Number.isInteger(alertAt) || alertAt < 1 || alertAt > 100) {
    return uni.showToast({ title: '提醒比例需在 1-100 之间', icon: 'none' })
  }
  const data = { name: form.name.trim(), amount, period: form.period, categoryId: form.categoryId,
    alertAt, isActive: form.isActive }
  saving.value = true
  try {
    if (id.value) await budgetApi.update(id.value, data)
    else await budgetApi.create(data)
    uni.navigateBack()
  } finally {
    saving.value = false
  }
}

async function remove() {
  const { confirm } = await uni.showModal({ title: '删除预算', content: '确定删除这个预算吗？' })
  if (!confirm) return
  await budgetApi.remove(id.value)
  uni.navigateBack()
}
</script>
