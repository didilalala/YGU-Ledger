/**
 * 支付通知解析。把通知监听插件回调的 { pkg, title, text, postTime } 解析为账单草稿。
 *
 * 规则需要用真实通知样本补充和校正（微信 / 支付宝的文案会随版本变化），
 * 每条新规则都要在 tests/parser.test.js 中加样例。
 * 参考原项目 litenote-mobile-app/src/services/paymentNotification/ 中的解析逻辑。
 */

export const PACKAGES = {
  WECHAT: 'com.tencent.mm',
  ALIPAY: 'com.eg.android.AlipayGphone',
}

const AMOUNT = '(\\d+(?:\\.\\d{1,2})?)'

/** 每条规则：匹配的包名、正则（作用于 title + 换行 + text）、收支类型、商户所在的捕获组 */
const RULES = [
  { pkg: PACKAGES.WECHAT, type: 'expense', pattern: new RegExp(`微信支付[\\s\\S]*?支付[￥¥]?${AMOUNT}元?`) },
  { pkg: PACKAGES.WECHAT, type: 'expense', pattern: new RegExp(`已支付[￥¥]${AMOUNT}`) },
  { pkg: PACKAGES.WECHAT, type: 'income', pattern: new RegExp(`微信支付收款${AMOUNT}元`) },
  { pkg: PACKAGES.ALIPAY, type: 'expense', pattern: new RegExp(`(?:付款|支付)${AMOUNT}元`) },
  { pkg: PACKAGES.ALIPAY, type: 'income', pattern: new RegExp(`成功收款${AMOUNT}元`) },
]

/**
 * @param {{pkg: string, title?: string, text?: string, postTime?: number}} notification
 * @returns {{amount: number, type: 'income'|'expense', description: string, date: string, source: 'notification', raw: string} | null}
 */
export function parseNotification(notification) {
  const raw = `${notification.title || ''}\n${notification.text || ''}`
  for (const rule of RULES) {
    if (rule.pkg !== notification.pkg) continue
    const match = raw.match(rule.pattern)
    if (!match) continue
    const amount = Number(match[1])
    if (!(amount > 0)) continue
    const time = new Date(notification.postTime || Date.now())
    return {
      amount,
      type: rule.type,
      description: notification.title || (notification.pkg === PACKAGES.WECHAT ? '微信支付' : '支付宝'),
      date: `${time.getFullYear()}-${String(time.getMonth() + 1).padStart(2, '0')}-${String(time.getDate()).padStart(2, '0')}`,
      source: 'notification',
      raw,
    }
  }
  return null
}

/**
 * 去重：同一笔支付常会触发多条通知。窗口期内金额与类型相同即视为重复。
 * @param {number} windowMs 默认 3 分钟
 */
export function createDeduplicator(windowMs = 3 * 60 * 1000) {
  const recent = []
  return (bill, now = Date.now()) => {
    while (recent.length && now - recent[0].at > windowMs) recent.shift()
    const key = `${bill.type}:${bill.amount}`
    if (recent.some((r) => r.key === key)) return true
    recent.push({ key, at: now })
    return false
  }
}
