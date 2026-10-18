<template>
  <view class="page">
    <ln-navbar :title="title" />

    <view class="content">
      <!-- 支出 / 收入 -->
      <view class="type-selector">
        <view :class="['type-btn', { expense: form.type === 'expense' }]" @click="switchType('expense')"><text>支出</text></view>
        <view :class="['type-btn', { income: form.type === 'income' }]" @click="switchType('income')"><text>收入</text></view>
      </view>

      <view class="group">
        <text class="group-label">💰 金额</text>
        <view class="amount-box">
          <text class="currency mono">¥</text>
          <input v-model="form.amount" class="amount-input mono" type="digit" placeholder="0.00" placeholder-class="ph" :focus="!id" />
        </view>
      </view>

      <view class="group">
        <text class="group-label">📂 分类</text>
        <view class="cat-grid">
          <view v-for="c in categories" :key="c.id" :class="['cat', { selected: form.categoryId === c.id }]" @click="form.categoryId = c.id">
            <text class="cat-icon">{{ c.icon || '📝' }}</text>
            <text class="cat-name">{{ c.name }}</text>
          </view>
          <view class="cat" @click="goAddCategory"><text class="cat-icon">➕</text><text class="cat-name">其他</text></view>
        </view>
      </view>

      <view class="group">
        <text class="group-label">📅 日期</text>
        <picker mode="date" :value="form.date" @change="(e) => (form.date = e.detail.value)">
          <view class="box between"><text class="mono">{{ form.date }}</text><ln-icon name="calendar" :size="36" /></view>
        </picker>
      </view>

      <view v-if="accounts.length" class="group">
        <text class="group-label">🏦 账户</text>
        <picker :range="accountOptions" range-key="label" :value="accountIndex" @change="(e) => (form.accountId = accountOptions[e.detail.value].id)">
          <view class="box between"><text>{{ accountOptions[accountIndex].label }}</text><ln-icon name="chevron-down" :size="36" /></view>
        </picker>
      </view>

      <view class="group">
        <text class="group-label">📝 备注</text>
        <textarea v-model="form.description" class="textarea" placeholder="添加备注..." placeholder-class="ph" :maxlength="200" auto-height />
      </view>

      <view class="group">
        <text class="group-label">🏷️ 标签</text>
        <input v-model="tagsText" class="box" placeholder="可选，空格或逗号分隔，最多 5 个" placeholder-class="ph" />
      </view>
    </view>

    <view class="bottom-actions">
      <view class="btn" @click="back">取消</view>
      <view :class="['btn btn-primary', { disabled: saving }]" @click="save">{{ saving ? '保存中…' : id ? '更新账单' : '保存' }}</view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { accountApi, billApi } from '@/api'
import { useCategoryStore } from '@/stores/category'
import { toDateString } from '@/utils/format'
import { formatTags, parseTags } from '@/utils/tags'

const categoryStore = useCategoryStore()
const saving = ref(false)
const tagsText = ref('')
const form = reactive({
  type: 'expense',
  amount: '',
  categoryId: null,
  date: toDateString(),
  description: '',
  accountId: null,
})

// 账户是可选的；新建账单时默认选中默认账户。注意余额不会随账单自动变化（与原项目一致）
const accounts = ref([])
const accountOptions = computed(() => [{ id: null, label: '不选择' }, ...accounts.value.map((a) => ({ id: a.id, label: a.name }))])
const accountIndex = computed(() => Math.max(0, accountOptions.value.findIndex((o) => o.id === form.accountId)))

const categories = computed(() => (form.type === 'expense' ? categoryStore.expense : categoryStore.income))

function switchType(type) {
  form.type = type
  form.categoryId = null
}

// 带 id 进入时是编辑模式：先取回账单填充表单
const id = ref(null)
const title = computed(() => (id.value ? '编辑账单' : '记一笔'))
const goAddCategory = () => uni.navigateTo({ url: `/pages/category/edit?type=${form.type}` })

onLoad(async (query) => {
  await categoryStore.load().catch(() => {})
  accounts.value = await accountApi.list().catch(() => [])
  if (!query.id) {
    form.accountId = accounts.value.find((a) => a.isDefault)?.id ?? null
    return
  }
  id.value = Number(query.id)
  const bill = await billApi.detail(id.value)
  Object.assign(form, {
    type: bill.type,
    amount: String(bill.amount),
    categoryId: bill.category?.id ?? null,
    date: bill.date,
    description: bill.description || '',
    accountId: bill.accountId ?? null,
  })
  tagsText.value = formatTags(bill.tags)
})

const back = () => uni.navigateBack()

async function save() {
  if (saving.value) return
  const amount = Number(form.amount)
  if (!(amount > 0)) return uni.showToast({ title: '请输入正确的金额', icon: 'none' })

  const tags = parseTags(tagsText.value)
  saving.value = true
  try {
    // 编辑时只提交表单里的字段，不改动来源等
    if (id.value) await billApi.update(id.value, { ...form, amount, tags })
    else await billApi.create({ ...form, amount, tags, source: 'manual' })
    uni.showToast({ title: id.value ? '已保存' : '已记账', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 500)
  } catch (e) {
    // 错误提示已由请求层统一处理
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.page {
  padding-bottom: calc(200rpx + env(safe-area-inset-bottom));
}
.content {
  padding: 32rpx;
}
.type-selector {
  display: flex;
  width: 62%;
  margin: 0 auto 40rpx;
  padding: 8rpx;
  background: $ln-card;
  @include brutal-box($ln-r-md, $ln-bw-thin);
}
.type-btn {
  flex: 1;
  padding: 20rpx 0;
  text-align: center;
  font-size: 32rpx;
  font-weight: 700;
  color: $ln-text-secondary;
  border: $ln-bw-thin solid transparent;
  border-radius: $ln-r-sm;
  &.expense,
  &.income {
    color: #fff;
    font-weight: 800;
    border-color: $ln-stroke;
  }
  &.expense {
    background: $ln-error;
  }
  &.income {
    background: $ln-success;
  }
}
.group {
  margin-bottom: 40rpx;
}
.group-label {
  display: block;
  margin-bottom: 16rpx;
  font-size: 28rpx;
  font-weight: 800;
}
.amount-box {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 32rpx;
  background: $ln-card;
  @include brutal-box($ln-r-lg);
}
.currency {
  font-size: 56rpx;
  font-weight: 800;
}
.amount-input {
  flex: 1;
  font-size: 56rpx;
  font-weight: 800;
}
.ph {
  color: $ln-text-secondary;
  font-weight: 500;
}
.cat-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}
.cat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: calc((100% - 60rpx) / 4);
  aspect-ratio: 1;
  background: $ln-card;
  @include brutal-box($ln-r-sm, $ln-bw-thin);
  &.selected {
    background: $ln-accent;
    border-width: $ln-bw;
  }
}
.cat-icon {
  margin-bottom: 8rpx;
  font-size: 48rpx;
}
.cat-name {
  font-size: 24rpx;
  font-weight: 600;
}
.cat.selected .cat-name {
  font-weight: 800;
}
.box {
  display: flex;
  align-items: center;
  width: 100%;
  min-height: 96rpx;
  padding: 0 28rpx;
  font-size: 30rpx;
  font-weight: 700;
  background: $ln-card;
  @include brutal-box($ln-r-md, $ln-bw-thin);
  &.between {
    justify-content: space-between;
  }
}
.textarea {
  width: 100%;
  min-height: 160rpx;
  padding: 24rpx 28rpx;
  font-size: 30rpx;
  font-weight: 600;
  background: $ln-card;
  @include brutal-box($ln-r-md, $ln-bw-thin);
}
.bottom-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  display: flex;
  gap: 24rpx;
  padding: 24rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
  background: $ln-bg;
  border-top: $ln-bw-thin solid $ln-stroke;
  .btn {
    flex: 1;
    &.disabled {
      opacity: 0.6;
    }
  }
}
</style>
