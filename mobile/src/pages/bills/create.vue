<template>
  <view>
    <view class="card">
      <uni-segmented-control :current="form.type === 'expense' ? 0 : 1" :values="['支出', '收入']"
        @clickItem="(e) => switchType(e.currentIndex === 0 ? 'expense' : 'income')" />
      <view class="amount-row">
        <text class="currency">¥</text>
        <input v-model="form.amount" class="amount-input" type="digit" placeholder="0.00" :focus="!id" />
      </view>
    </view>

    <view class="card">
      <text class="label">分类</text>
      <view class="categories">
        <view v-for="c in categories" :key="c.id" :class="['category', { active: form.categoryId === c.id }]"
          @click="form.categoryId = c.id">
          <text class="category-icon">{{ c.icon || '📝' }}</text>
          <text class="muted">{{ c.name }}</text>
        </view>
      </view>
    </view>

    <view class="card fields">
      <picker mode="date" :value="form.date" @change="(e) => (form.date = e.detail.value)">
        <view class="field"><text>日期</text><text class="muted">{{ form.date }} ›</text></view>
      </picker>
      <picker v-if="accounts.length" :range="accountOptions" range-key="label" :value="accountIndex"
        @change="(e) => (form.accountId = accountOptions[e.detail.value].id)">
        <view class="field"><text>账户</text><text class="muted">{{ accountOptions[accountIndex].label }} ›</text></view>
      </picker>
      <uni-easyinput v-model="form.description" placeholder="备注（可选）" />
      <uni-easyinput v-model="tagsText" placeholder="标签（可选，空格或逗号分隔，最多 5 个）" />
      <!-- TODO: 上传收据图片 -->
    </view>

    <view class="actions">
      <button class="primary" :loading="saving" :disabled="saving" @click="save">{{ id ? '保存修改' : '保存' }}</button>
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

onLoad(async (query) => {
  await categoryStore.load().catch(() => {})
  accounts.value = await accountApi.list().catch(() => [])
  if (!query.id) {
    form.accountId = accounts.value.find((a) => a.isDefault)?.id ?? null
    return
  }
  id.value = Number(query.id)
  uni.setNavigationBarTitle({ title: '编辑账单' })
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

async function save() {
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
.amount-row {
  display: flex;
  align-items: center;
  margin-top: 32rpx;
}
.currency {
  font-size: 48rpx;
  margin-right: 16rpx;
}
.amount-input {
  flex: 1;
  font-size: 64rpx;
  height: 96rpx;
  font-weight: 600;
}
.label {
  font-weight: 600;
}
.categories {
  display: flex;
  flex-wrap: wrap;
  margin-top: 16rpx;
}
.category {
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 0;
  border-radius: 16rpx;
  &.active {
    background: rgba(79, 110, 247, 0.12);
  }
}
.category-icon {
  font-size: 44rpx;
}
.fields {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}
.field {
  display: flex;
  justify-content: space-between;
  padding: 8rpx 0;
}
.actions {
  padding: 32rpx;
}
.primary {
  background: $ln-primary;
  color: #fff;
}
</style>
