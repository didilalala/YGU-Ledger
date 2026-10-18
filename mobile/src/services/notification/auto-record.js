/**
 * 支付通知自动记账服务。
 * 页面只负责开关和展示，监听、解析、去重、确认、入账都在这里，因此离开设置页后依然生效。
 *
 * 流程：插件回调 → 解析 → 去重 → 入队 → 弹窗确认 → 创建账单（source=notification）。
 * 开关状态保存在本地，App 启动时由 restoreAutoRecord() 恢复。
 *
 * ⚠️ 依赖的 UTS 插件尚未在真机验证，见 uni_modules/lite-notification-listener/README.md。
 */
import { billApi } from '@/api'
import { STORAGE_KEYS, storage } from '@/utils/storage'
import { createDeduplicator, PACKAGES, parseNotification } from './parser'
import { describeBill, toBillPayload } from './payload'
import { createSerialQueue } from './serial-queue'
// #ifdef APP-ANDROID
import { isListenerEnabled, startListening, stopListening } from '@/uni_modules/lite-notification-listener'
// #endif

const isDev = import.meta.env.DEV
const isDuplicate = createDeduplicator()
const queue = createSerialQueue()
const listeners = new Set()
let running = false

const emit = (event) => listeners.forEach((fn) => fn(event))

/** 订阅事件：{ kind: 'raw', info } 仅开发模式；{ kind: 'bill', bill, status: 'saved' | 'skipped' | 'failed' } */
export function onAutoRecordEvent(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

export const isAutoRecordEnabled = () => storage.get(STORAGE_KEYS.AUTO_RECORD, false) === true
export const isAutoRecordRunning = () => running

/** 系统是否已授予"通知使用权" */
export function hasListenerPermission() {
  // #ifdef APP-ANDROID
  return isListenerEnabled()
  // #endif
  // #ifndef APP-ANDROID
  return false
  // #endif
}

async function confirmAndSave(bill) {
  const { confirm } = await uni.showModal({
    title: '检测到一笔支付，是否记账？',
    content: describeBill(bill),
    confirmText: '记账',
    cancelText: '忽略',
  })
  if (!confirm) return emit({ kind: 'bill', bill, status: 'skipped' })
  try {
    await billApi.create(toBillPayload(bill))
    uni.showToast({ title: '已记账，可在账单中补充分类', icon: 'none' })
    emit({ kind: 'bill', bill, status: 'saved' })
  } catch (e) {
    emit({ kind: 'bill', bill, status: 'failed' }) // 失败原因已由请求层提示
  }
}

function handleNotification(info) {
  if (isDev) emit({ kind: 'raw', info })
  const bill = parseNotification(info)
  if (!bill || isDuplicate(bill)) return
  queue.push(() => confirmAndSave(bill)).catch(() => {})
}

/** 开始监听并记住开关。没有通知使用权或不在 Android 上时返回 false */
export function startAutoRecord() {
  // #ifdef APP-ANDROID
  if (!hasListenerPermission()) return false
  // 开发模式不过滤包名，便于用 adb 发测试通知验证链路
  startListening({ packages: isDev ? [] : [PACKAGES.WECHAT, PACKAGES.ALIPAY] }, handleNotification)
  running = true
  storage.set(STORAGE_KEYS.AUTO_RECORD, true)
  return true
  // #endif
  // #ifndef APP-ANDROID
  return false
  // #endif
}

export function stopAutoRecord() {
  // #ifdef APP-ANDROID
  stopListening()
  // #endif
  running = false
  storage.set(STORAGE_KEYS.AUTO_RECORD, false)
}

/** App 启动 / 登录后调用：上次开着就接着开。权限被用户在系统里撤销时保持关闭 */
export function restoreAutoRecord() {
  if (running || !isAutoRecordEnabled()) return false
  return startAutoRecord()
}

/** 退出登录时调用：停止监听，但不改动开关，下次登录自动恢复 */
export function suspendAutoRecord() {
  // #ifdef APP-ANDROID
  if (running) stopListening()
  // #endif
  running = false
}
