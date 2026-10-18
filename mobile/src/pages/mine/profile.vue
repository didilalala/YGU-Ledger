<template>
  <view>
    <view class="card">
      <view class="form-field" @click="chooseAvatar">
        <text class="label">头像</text>
        <view class="avatar-wrap">
          <image v-if="userStore.user?.avatar" class="avatar" :src="userStore.user.avatar" mode="aspectFill" />
          <view v-else class="avatar placeholder">{{ userStore.displayName.slice(0, 1) }}</view>
          <text class="muted">{{ uploading ? '上传中…' : '›' }}</text>
        </view>
      </view>
      <view class="form-field">
        <text class="label">用户名</text>
        <text class="muted">{{ userStore.user?.username }}</text>
      </view>
      <view class="form-field">
        <text class="label">昵称</text>
        <input v-model="form.nickname" placeholder="给自己起个名字" maxlength="50" />
      </view>
      <view class="form-field">
        <text class="label">邮箱</text>
        <input v-model="form.email" placeholder="选填" type="text" />
      </view>
    </view>
    <view class="form-actions">
      <button class="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { authApi } from '@/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const form = reactive({ nickname: '', email: '' })
const saving = ref(false)
const uploading = ref(false)

onShow(() => {
  form.nickname = userStore.user?.nickname || ''
  form.email = userStore.user?.email || ''
})

async function chooseAvatar() {
  if (uploading.value) return
  let path
  try {
    path = (await uni.chooseImage({ count: 1, sizeType: ['compressed'] })).tempFilePaths[0]
  } catch (e) {
    return // 取消选择
  }
  uploading.value = true
  try {
    userStore.setUser(await authApi.uploadAvatar(path))
    uni.showToast({ title: '头像已更新', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: e.message || '上传失败', icon: 'none' })
  } finally {
    uploading.value = false
  }
}

async function save() {
  const email = form.email.trim()
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
  }
  saving.value = true
  try {
    // 清空邮箱要传 null，后端把空字符串当作非法值
    userStore.setUser(await authApi.updateProfile({ nickname: form.nickname.trim(), email: email || null }))
    uni.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 500)
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.avatar-wrap {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  &.placeholder {
    background: $ln-primary;
    color: #fff;
    font-size: 44rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
