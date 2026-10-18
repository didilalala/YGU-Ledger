<template>
  <view class="card form">
    <uni-easyinput v-model="form.username" placeholder="用户名（3-50 位）" />
    <uni-easyinput v-model="form.nickname" placeholder="昵称（可选）" />
    <uni-easyinput v-model="form.password" type="password" placeholder="密码（至少 6 位）" />
    <uni-easyinput v-model="confirm" type="password" placeholder="确认密码" />
    <button class="primary" :loading="loading" :disabled="loading" @click="submit">注册</button>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const form = reactive({ username: '', nickname: '', password: '' })
const confirm = ref('')
const loading = ref(false)

async function submit() {
  if (form.username.trim().length < 3) return uni.showToast({ title: '用户名至少 3 位', icon: 'none' })
  if (form.password.length < 6) return uni.showToast({ title: '密码至少 6 位', icon: 'none' })
  if (form.password !== confirm.value) return uni.showToast({ title: '两次密码不一致', icon: 'none' })

  loading.value = true
  try {
    await userStore.register({ ...form, username: form.username.trim() })
    uni.switchTab({ url: '/pages/dashboard/index' })
  } catch (e) {
    // 错误提示已由请求层统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}
.primary {
  background: $ln-primary;
  color: #fff;
}
</style>
