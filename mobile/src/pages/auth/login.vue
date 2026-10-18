<template>
  <view class="page">
    <view class="logo-section">
      <view class="logo-box"><image class="logo" src="/static/logo.jpg" mode="aspectFill" /></view>
      <text class="app-title">LiteNote</text>
      <text class="subtitle">你的生活理财助手</text>
    </view>

    <view class="form-card">
      <view class="mode-toggle">
        <view :class="['mode-btn', { active: mode === 'login' }]" @click="switchMode('login')"><text>登录</text></view>
        <view :class="['mode-btn', { active: mode === 'register' }]" @click="switchMode('register')"><text>注册</text></view>
      </view>

      <view class="input-group">
        <view class="input-wrap">
          <input v-model="form.username" :class="['input', { error: errors.username }]" placeholder="用户名"
            placeholder-class="ph" @input="errors.username = ''" />
          <text v-if="errors.username" class="field-error">{{ errors.username }}</text>
        </view>
        <view class="input-wrap">
          <input v-model="form.password" :class="['input', { error: errors.password }]" password placeholder="密码"
            placeholder-class="ph" @input="errors.password = ''" />
          <text v-if="errors.password" class="field-error">{{ errors.password }}</text>
        </view>
        <template v-if="mode === 'register'">
          <view class="input-wrap">
            <input v-model="form.confirmPassword" :class="['input', { error: errors.confirmPassword }]" password
              placeholder="确认密码" placeholder-class="ph" @input="errors.confirmPassword = ''" />
            <text v-if="errors.confirmPassword" class="field-error">{{ errors.confirmPassword }}</text>
          </view>
          <view class="input-wrap">
            <input v-model="form.nickname" class="input" placeholder="昵称（选填）" placeholder-class="ph" />
          </view>
        </template>
      </view>

      <view v-if="errorMessage" class="error-box"><text>{{ errorMessage }}</text></view>

      <button class="submit" :disabled="loading" @click="submit">{{ loading ? '请稍候…' : mode === 'login' ? '登录' : '注册' }}</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { validateAuthForm } from '@/utils/auth-form'

const userStore = useUserStore()
const mode = ref('login') // login | register
const form = reactive({ username: '', password: '', confirmPassword: '', nickname: '' })
const errors = reactive({ username: '', password: '', confirmPassword: '' })
const errorMessage = ref('')
const loading = ref(false)

function switchMode(next) {
  mode.value = next
  errorMessage.value = ''
  Object.assign(errors, { username: '', password: '', confirmPassword: '' })
}

async function submit() {
  const found = validateAuthForm(mode.value, form)
  Object.assign(errors, { username: '', password: '', confirmPassword: '', ...found })
  if (Object.keys(found).length) return

  errorMessage.value = ''
  loading.value = true
  try {
    const username = form.username.trim()
    if (mode.value === 'login') await userStore.login(username, form.password)
    else await userStore.register({ username, password: form.password, nickname: form.nickname.trim() })
    uni.switchTab({ url: '/pages/dashboard/index' })
  } catch (e) {
    errorMessage.value = e.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: calc(var(--status-bar-height) + 48rpx) 40rpx 64rpx;
}
.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 48rpx;
}
.logo-box {
  width: 168rpx;
  height: 168rpx;
  margin-bottom: 32rpx;
  overflow: hidden;
  background: $ln-accent;
  @include brutal-box($ln-r-lg, $ln-bw-thick);
  @include brutal-shadow(8rpx);
}
.logo {
  width: 100%;
  height: 100%;
}
.app-title {
  font-size: 64rpx;
  font-weight: 900;
  letter-spacing: -1rpx;
}
.subtitle {
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: $ln-text-secondary;
}
.form-card {
  padding: 40rpx;
  background: $ln-card;
  @include brutal-box($ln-r-lg);
  @include brutal-shadow(8rpx);
  margin-right: 8rpx;
}
.mode-toggle {
  display: flex;
  margin-bottom: 40rpx;
  overflow: hidden;
  @include brutal-box($ln-r-md, $ln-bw-thin);
}
.mode-btn {
  flex: 1;
  padding: 22rpx 0;
  text-align: center;
  font-size: 30rpx;
  font-weight: 700;
  color: $ln-text-secondary;
  background: $ln-card;
  &.active {
    color: #fff;
    background: $ln-primary;
  }
}
.input-group {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  margin-bottom: 32rpx;
}
.input {
  width: 100%;
  min-height: 96rpx;
  padding: 0 32rpx;
  font-size: 30rpx;
  font-weight: 600;
  background: $ln-bg;
  @include brutal-box($ln-r-md, $ln-bw-thin);
  &.error {
    border-color: $ln-error;
  }
}
.ph {
  color: $ln-text-secondary;
  font-weight: 500;
}
.field-error {
  display: block;
  margin: 8rpx 0 0 16rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: $ln-error;
}
.error-box {
  padding: 20rpx;
  margin-bottom: 24rpx;
  text-align: center;
  font-size: 28rpx;
  font-weight: 600;
  color: $ln-error;
  background: $ln-expense-bg;
  border: $ln-bw-thin solid $ln-error;
  border-radius: $ln-r-sm;
}
.submit {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 104rpx;
  margin: 0;
  font-size: 32rpx;
  font-weight: 800;
  color: #fff;
  background: $ln-primary;
  @include brutal-box($ln-r-md);
  @include brutal-shadow(6rpx);
  @include brutal-press(6rpx);
  &::after {
    display: none;
  }
  &[disabled] {
    background: $ln-text-quaternary;
    box-shadow: none;
  }
}
</style>
