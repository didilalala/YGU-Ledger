<template>
  <view class="page">
    <ln-navbar :title="'修改密码'" />
    <view class="form">
      <view class="form-field">
        <text class="label">原密码</text>
        <input v-model="form.oldPassword" password placeholder="请输入原密码" />
      </view>
      <view class="form-field">
        <text class="label">新密码</text>
        <input v-model="form.newPassword" password placeholder="至少 6 位" />
      </view>
      <view class="form-field">
        <text class="label">确认新密码</text>
        <input v-model="form.confirm" password placeholder="再输入一次" />
      </view>
    </view>
    <view class="form-actions">
      <button class="primary" :disabled="saving" @click="save">{{ saving ? '提交中…' : '修改密码' }}</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { authApi } from '@/api'

const form = reactive({ oldPassword: '', newPassword: '', confirm: '' })
const saving = ref(false)

async function save() {
  if (!form.oldPassword) return uni.showToast({ title: '请输入原密码', icon: 'none' })
  if (form.newPassword.length < 6) return uni.showToast({ title: '新密码至少 6 位', icon: 'none' })
  if (form.newPassword !== form.confirm) return uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' })
  if (form.newPassword === form.oldPassword) return uni.showToast({ title: '新密码不能和原密码相同', icon: 'none' })
  saving.value = true
  try {
    await authApi.changePassword({ oldPassword: form.oldPassword, newPassword: form.newPassword })
    uni.showToast({ title: '密码已修改', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 800)
  } finally {
    saving.value = false
  }
}
</script>
