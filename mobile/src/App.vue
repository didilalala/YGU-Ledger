<script>
import { restoreAutoRecord } from '@/services/notification/auto-record'
import { storage, STORAGE_KEYS } from '@/utils/storage'
import { checkUpdate } from '@/utils/update'

export default {
  onLaunch() {
    // 启动页是首页（tabBar 页），未登录时直接切到登录页
    if (!storage.get(STORAGE_KEYS.TOKEN)) {
      uni.reLaunch({ url: '/pages/auth/login' })
    } else {
      restoreAutoRecord() // 上次开着通知自动记账的话，启动后接着开
    }
    // #ifdef APP-PLUS
    checkUpdate({ silent: true }) // 静默检查：只在有更新时才打扰用户
    // #endif
  },
}
</script>

<style lang="scss">
/* ========== 全局样式（Claymorphism 黏土拟态） ========== */
page {
  background-color: $ln-bg;
  color: $ln-text;
  font-family: $ln-font;
  font-size: 28rpx;
}

view,
text,
input,
button,
scroll-view,
swiper,
image,
picker {
  box-sizing: border-box;
  font-family: inherit;
}

/* 带底部导航的页面：给自绘 tabbar 留出空间 */
.has-tabbar {
  padding-bottom: calc(190rpx + env(safe-area-inset-bottom));
}

/* 卡片：白色黏土块，大圆角 + 柔和浮起 */
.card {
  background: $ln-card;
  padding: 32rpx;
  margin: 24rpx 32rpx 36rpx;
  @include clay-box($ln-r-lg);
  @include clay-shadow(8rpx);
}

/* 表单页：字段直接放在背景上，不套卡片 */
.form {
  padding: 16rpx 32rpx 0;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  padding: 14rpx 0;
  .label {
    display: block;
    font-size: 28rpx;
    font-weight: 800;
  }
  picker {
    display: block;
    width: 100%;
  }
  input,
  .value {
    width: 100%;
    min-height: 96rpx;
    padding: 0 28rpx;
    display: flex;
    align-items: center;
    font-size: 30rpx;
    font-weight: 700;
    color: $ln-text;
    background: $ln-card;
    border-radius: $ln-r-md;
    @include clay-inset(6rpx); /* 输入框是凹进去的 */
  }
  .value {
    justify-content: space-between;
    color: $ln-text;
    &.readonly {
      color: $ln-text-secondary;
      background: $ln-border;
    }
  }
  /* 开关等"标签在左、控件在右"的行 */
  &.row {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
  .hint {
    display: block;
    margin-top: 4rpx;
    font-size: 24rpx;
    color: $ln-text-secondary;
  }
}

/* 按钮：鼓鼓的黏土块，按下时捏扁一点 */
.btn,
.form-actions button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  min-height: 96rpx;
  margin: 0;
  padding: 0 40rpx;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 1;
  color: $ln-text;
  background: $ln-card;
  @include clay-box($ln-r-md);
  @include clay-shadow(6rpx);
  @include clay-press(6rpx);
  &::after {
    display: none; /* uni 的 button 自带一圈边框，去掉 */
  }
  &[disabled] {
    color: $ln-text-secondary;
    background: $ln-border;
    @include clay-inset(4rpx);
  }
}
.btn-primary,
.form-actions .primary {
  color: #fff;
  text-shadow: 0 2rpx 0 rgba(70, 40, 160, 0.35);
  background: $ln-primary;
}
.btn-accent {
  background: $ln-accent;
}
.btn-sm {
  min-height: 64rpx;
  padding: 0 28rpx;
  font-size: 26rpx;
  border-radius: $ln-r-sm;
  @include clay-shadow(4rpx);
}
.form-actions {
  padding: 32rpx 32rpx 48rpx;
  button + button {
    margin-top: 32rpx;
  }
  .danger {
    color: $ln-error;
    background: $ln-card;
  }
}

/* 徽章：小块的黏土标签，如金额、百分比 */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 6rpx 20rpx;
  font-size: 26rpx;
  font-weight: 800;
  font-family: $ln-mono;
  background: $ln-accent;
  @include clay-box($ln-r-sm, $ln-bw-thin);
  &.income {
    color: $ln-income;
    background: $ln-income-bg;
  }
  &.expense {
    color: $ln-expense;
    background: $ln-expense-bg;
  }
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

.mono {
  font-family: $ln-mono;
}

.empty-tip {
  padding: 64rpx 0;
  text-align: center;
  color: $ln-text-secondary;
  font-weight: 700;
}
</style>
