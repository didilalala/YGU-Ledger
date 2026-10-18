<template>
  <view class="page">
    <view class="brand">
      <text class="logo">LiteNote</text>
      <text class="muted">AI 智能记账</text>
    </view>

    <view class="card form">
      <uni-easyinput v-model="form.username" placeholder="用户名" :input-border="false" />
      <uni-easyinput v-model="form.password" type="password" placeholder="密码" :input-border="false" />
      <button class="primary" :loading="loading" :disabled="loading" @click="submit">登录</button>
      <view class="switch muted" @click="goRegister">还没有账号？去注册</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) {
    uni.showToast({ title: '请输入用户名和密码', icon: 'none' })
    return
  }
  loading.value = true
  try {
    await userStore.login(form.username.trim(), form.password)
    uni.switchTab({ url: '/pages/dashboard/index' })
  } catch (e) {
    // 错误提示已由请求层统一处理
  } finally {
    loading.value = false
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/auth/register' })
}
</script>

<style lang="scss" scoped>
.page {
  padding-top: 240rpx;
}
.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 64rpx;
  gap: 12rpx;
}
.logo {
  font-size: 56rpx;
  font-weight: 700;
  color: $ln-primary;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}
.primary {
  background: $ln-primary;
  color: #fff;
  margin-top: 16rpx;
}
.switch {
  text-align: center;
}
</style>
