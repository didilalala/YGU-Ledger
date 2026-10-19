<template>
  <view v-if="visible" class="mask" @click="$emit('close')">
    <view class="sheet" @click.stop>
      <view class="head">
        <text class="title">修改账单</text>
        <view class="close" @click="$emit('close')"><ln-icon name="x" :size="36" /></view>
      </view>

      <view class="body">
        <view class="field">
          <text class="label">金额</text>
          <input v-model="form.amount" class="box" type="digit" placeholder="金额" />
        </view>
        <view class="field">
          <text class="label">描述</text>
          <input v-model="form.description" class="box" placeholder="简短描述" />
        </view>
        <view class="field">
          <text class="label">分类</text>
          <picker :range="options" range-key="label" :value="categoryIndex" @change="onCategory">
            <view class="box between"><text>{{ options[categoryIndex]?.label || '请选择分类' }}</text><ln-icon name="chevron-down" :size="32" /></view>
          </picker>
        </view>
        <view class="field">
          <text class="label">日期</text>
          <picker mode="date" :value="form.date" @change="form.date = $event.detail.value">
            <view class="box between"><text>{{ form.date }}</text><ln-icon name="calendar" :size="32" /></view>
          </picker>
        </view>
      </view>

      <view class="foot">
        <view class="btn" @click="$emit('close')">取消</view>
        <view class="btn btn-primary" @click="save">保存</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'

/** 修改 AI 识别出的账单（保存前）：底部弹出，对应原项目 EditBillModal */
const props = defineProps({
  visible: { type: Boolean, default: false },
  bill: { type: Object, default: null },
  categories: { type: Array, default: () => [] }, // 全部分类，按账单类型过滤
})
const emit = defineEmits(['close', 'save'])

const form = reactive({ amount: '', description: '', date: '', categoryId: null })

watch(() => [props.visible, props.bill], () => {
  if (!props.visible || !props.bill) return
  Object.assign(form, {
    amount: String(props.bill.amount), description: props.bill.description || '',
    date: props.bill.date, categoryId: props.bill.categoryId ?? null,
  })
}, { immediate: true })

const options = computed(() => props.categories
  .filter((c) => c.type === props.bill?.type)
  .map((c) => ({ id: c.id, label: `${c.icon || ''} ${c.name}`, category: c })))
const categoryIndex = computed(() => Math.max(0, options.value.findIndex((o) => o.id === form.categoryId)))

const onCategory = (e) => { form.categoryId = options.value[e.detail.value].id }

function save() {
  const amount = Number(form.amount)
  if (!(amount > 0)) return uni.showToast({ title: '请输入正确的金额', icon: 'none' })
  const picked = options.value.find((o) => o.id === form.categoryId)?.category
  emit('save', {
    ...props.bill, amount, description: form.description.trim(), date: form.date,
    categoryId: picked?.id ?? null, categoryName: picked?.name ?? props.bill.categoryName, categoryIcon: picked?.icon ?? props.bill.categoryIcon,
  })
}
</script>

<style lang="scss" scoped>
.mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  background: rgba(47, 42, 92, 0.45);
}
.sheet {
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  background: $ln-card;
  border-radius: $ln-r-lg $ln-r-lg 0 0;
  box-shadow: 0 -12rpx 40rpx rgba(120, 100, 190, 0.3);
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
}
.title {
  font-size: 38rpx;
  font-weight: 800;
}
.close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  @include clay-box($ln-r-sm, $ln-bw-thin);
}
.body {
  padding: 16rpx 32rpx;
}
.field {
  padding: 14rpx 0;
}
.label {
  display: block;
  margin-bottom: 12rpx;
  font-size: 28rpx;
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
  border-radius: $ln-r-md;
  @include clay-inset(6rpx);
  &.between {
    justify-content: space-between;
  }
}
.foot {
  display: flex;
  gap: 24rpx;
  padding: 24rpx 32rpx calc(40rpx + env(safe-area-inset-bottom));
  .btn {
    flex: 1;
  }
}
</style>
