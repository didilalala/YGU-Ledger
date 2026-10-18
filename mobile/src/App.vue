<script>
import { storage, STORAGE_KEYS } from '@/utils/storage'

export default {
  onLaunch() {
    // 启动页是首页（tabBar 页），未登录时直接切到登录页
    if (!storage.get(STORAGE_KEYS.TOKEN)) {
      uni.reLaunch({ url: '/pages/auth/login' })
    }
    // TODO: 已开启通知自动记账时，在这里启动监听（见 services/notification）
  },
}
</script>

<style lang="scss">
/* 全局样式 */
page {
  background-color: $ln-bg;
  color: $ln-text;
  font-size: 28rpx;
}

.card {
  background: $ln-card;
  border-radius: 24rpx;
  padding: 32rpx;
  margin: 24rpx 32rpx;
}

.income {
  color: $ln-income;
}

.expense {
  color: $ln-expense;
}

.muted {
  color: $ln-text-secondary;
  font-size: 24rpx;
}
</style>
