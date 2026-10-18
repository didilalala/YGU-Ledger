<template>
  <view class="ln-chart" :style="{ width: width + 'px', height: height + 'px' }">
    <!-- 绘图缓冲区放大 pixelRatio 倍再缩小显示，高分屏上才清晰 -->
    <canvas :id="canvasId" :canvas-id="canvasId" :style="canvasStyle" />
  </view>
</template>

<script setup>
import { computed, getCurrentInstance, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import { buildChartOptions, createChart } from '@/utils/chart'

const props = defineProps({
  type: { type: String, required: true }, // ring | pie | line | column
  series: { type: Array, required: true },
  categories: { type: Array, default: () => [] },
  /** 显示宽高，单位 rpx；默认宽度刚好撑满带内边距的卡片 */
  widthRpx: { type: Number, default: 622 },
  heightRpx: { type: Number, default: 480 },
  /** 圆环中心的文字，如 { title: '¥4550', subtitle: '总计' } */
  center: { type: Object, default: null },
})

const canvasId = `ln-chart-${Math.random().toString(36).slice(2, 9)}`
const instance = getCurrentInstance()

const windowWidth = (uni.getWindowInfo ? uni.getWindowInfo() : uni.getSystemInfoSync()).windowWidth
const pixelRatio = Math.min(uni.getSystemInfoSync().pixelRatio || 1, 3)
const width = computed(() => Math.round((props.widthRpx * windowWidth) / 750))
const height = computed(() => Math.round((props.heightRpx * windowWidth) / 750))
const canvasStyle = computed(() => ({
  width: `${width.value * pixelRatio}px`,
  height: `${height.value * pixelRatio}px`,
  transform: `scale(${1 / pixelRatio})`,
  transformOrigin: '0 0',
}))

let chart = null

function draw() {
  // 数据快速变化时，上一次的动画还没播完，先停掉避免两帧叠在一起
  chart?.animationInstance?.stop?.()
  const context = uni.createCanvasContext(canvasId, instance.proxy)
  chart = createChart(context, buildChartOptions({
    type: props.type,
    categories: props.categories,
    series: props.series,
    width: width.value * pixelRatio,
    height: height.value * pixelRatio,
    pixelRatio,
    center: props.center,
  }))
}

// canvas 节点渲染完成后再画；App 端偶尔需要再等一帧
onMounted(() => nextTick(() => setTimeout(draw, 30)))
watch(() => [props.type, props.series, props.categories, props.center], () => nextTick(draw), { deep: true })
onBeforeUnmount(() => chart?.animationInstance?.stop?.())
</script>

<style lang="scss" scoped>
.ln-chart {
  position: relative;
  overflow: hidden;
  margin: 0 auto;
}
</style>
