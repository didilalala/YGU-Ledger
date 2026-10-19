<template>
  <view class="page">
    <ln-navbar :title="id ? '编辑目标' : '新建目标'" />
    <view class="form">
      <view class="form-field">
        <text class="label">名称</text>
        <input v-model="form.name" placeholder="如：旅行基金" />
      </view>
      <view class="form-field">
        <text class="label">图标</text>
        <input v-model="form.icon" placeholder="一个 emoji，如 ✈️" maxlength="4" />
      </view>
      <view class="form-field">
        <text class="label">目标金额</text>
        <input v-model="form.targetAmount" type="digit" placeholder="要攒多少" />
      </view>
      <view class="form-field">
        <text class="label">已存金额</text>
        <input v-model="form.currentAmount" type="digit" placeholder="0" />
      </view>
      <view class="form-field">
        <text class="label">截止日期</text>
        <view class="deadline">
          <picker mode="date" :value="form.deadline" @change="form.deadline = $event.detail.value">
            <view class="value">{{ form.deadline || '不限 ›' }}</view>
          </picker>
          <text v-if="form.deadline" class="muted clear" @click="form.deadline = ''">清除</text>
        </view>
      </view>
      <view class="form-field row">
        <text class="label">已完成</text>
        <switch :checked="form.isCompleted" color="#2A9D76" @change="form.isCompleted = $event.detail.value" />
      </view>
    </view>
    <view class="form-actions">
      <button class="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
      <button v-if="id" class="danger" @click="remove">删除目标</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { goalApi } from '@/api'

const id = ref(null)
const saving = ref(false)
const form = reactive({ name: '', icon: '', targetAmount: '', currentAmount: '', deadline: '', isCompleted: false })

onLoad(async (query) => {
  if (!query.id) return
  id.value = Number(query.id)
  const g = (await goalApi.list()).find((x) => x.id === id.value)
  if (!g) return uni.navigateBack()
  Object.assign(form, { name: g.name, icon: g.icon || '', targetAmount: String(g.targetAmount),
    currentAmount: String(g.currentAmount), deadline: g.deadline || '', isCompleted: g.isCompleted })
})

async function save() {
  const target = Number(form.targetAmount)
  const current = Number(form.currentAmount || 0)
  if (!form.name.trim()) return uni.showToast({ title: '请填写名称', icon: 'none' })
  if (!(target > 0)) return uni.showToast({ title: '请填写大于 0 的目标金额', icon: 'none' })
  if (!(current >= 0)) return uni.showToast({ title: '已存金额不能为负', icon: 'none' })
  const data = {
    name: form.name.trim(),
    icon: form.icon.trim() || null,
    targetAmount: target,
    currentAmount: current,
    deadline: form.deadline || null,
    // 攒够了就自动标记完成；用户也可以手动勾选
    isCompleted: form.isCompleted || current >= target,
  }
  saving.value = true
  try {
    if (id.value) await goalApi.update(id.value, data)
    else await goalApi.create(data)
    uni.navigateBack()
  } finally {
    saving.value = false
  }
}

async function remove() {
  const { confirm } = await uni.showModal({ title: '删除目标', content: '确定删除这个目标吗？' })
  if (!confirm) return
  await goalApi.remove(id.value)
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.deadline {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
</style>
