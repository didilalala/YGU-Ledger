<template>
  <view class="page">
    <ln-navbar :title="id ? '编辑分类' : '添加分类'" />
    <view class="form">
      <view class="form-field">
        <text class="label">类型</text>
        <view class="value readonly"><text>{{ form.type === 'expense' ? '支出' : '收入' }}{{ id ? '（不可修改）' : '' }}</text></view>
      </view>
      <view class="form-field">
        <text class="label">名称</text>
        <input v-model="form.name" placeholder="如：宠物" maxlength="20" />
      </view>
      <view class="form-field">
        <text class="label">图标</text>
        <input v-model="form.icon" placeholder="一个 emoji，如 🐶" maxlength="4" />
      </view>
      <view class="presets">
        <text v-for="e in PRESET_ICONS" :key="e" :class="['preset', { on: form.icon === e }]" @click="form.icon = e">{{ e }}</text>
      </view>
    </view>
    <view class="form-actions">
      <button class="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
      <button v-if="id" class="danger" @click="remove">删除分类</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { categoryApi } from '@/api'
import { useCategoryStore } from '@/stores/category'

const PRESET_ICONS = ['🍜', '☕', '🛒', '🚌', '🏠', '🎬', '💊', '📚', '🐶', '👶', '✈️', '🎁', '💰', '📈', '💼', '🧾']

const store = useCategoryStore()
const id = ref(null)
const saving = ref(false)
const form = reactive({ name: '', icon: '', type: 'expense' })

onLoad(async (query) => {
  if (!query.id) {
    form.type = query.type === 'income' ? 'income' : 'expense'
    return
  }
  id.value = Number(query.id)
  await store.load()
  const c = store.list.find((x) => x.id === id.value)
  if (!c || c.isDefault) return uni.navigateBack()
  Object.assign(form, { name: c.name, icon: c.icon || '', type: c.type })
})

async function save() {
  const name = form.name.trim()
  if (!name) return uni.showToast({ title: '请填写名称', icon: 'none' })
  const duplicated = store.list.some((c) => c.id !== id.value && c.type === form.type && c.name === name)
  if (duplicated) return uni.showToast({ title: '已有同名分类', icon: 'none' })
  const data = { name, icon: form.icon.trim() || null }
  saving.value = true
  try {
    if (id.value) await categoryApi.update(id.value, data)
    else await categoryApi.create({ ...data, type: form.type })
    await store.load(true)
    uni.navigateBack()
  } finally {
    saving.value = false
  }
}

async function remove() {
  const { confirm } = await uni.showModal({
    title: '删除分类',
    content: '该分类下已有的账单会变成“未分类”，确定删除吗？',
  })
  if (!confirm) return
  await categoryApi.remove(id.value)
  await store.load(true)
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.presets {
  display: flex;
  flex-wrap: wrap;
  padding-top: 16rpx;
}
.preset {
  width: 12.5%;
  text-align: center;
  font-size: 40rpx;
  padding: 12rpx 0;
  border-radius: $ln-r-sm;
  &.on {
    background: $ln-primary-light;
  }
}
</style>
