/**
 * AI 流式对话（SSE over POST）。
 *
 * ⚠️ 这是 PoC 代码，需要在真机验证（见改造方案 8.4 节）：
 * - App 端依赖 uni.request 的 enableChunked + onChunkReceived，需确认当前基座版本支持
 * - H5 端用 fetch + ReadableStream
 * 如果 App 端不可用，退回到 aiApi.send（非流式）。
 */
import { API_BASE_URL } from '@/config/env'
import { authHeader } from './http'

/** 把收到的文本块按 SSE 协议切分成事件，不完整的尾部留到下次 */
export function createSSEParser(onEvent) {
  let buffer = ''
  return (chunk) => {
    buffer += chunk
    const parts = buffer.split('\n\n')
    buffer = parts.pop()
    for (const part of parts) {
      const line = part.split('\n').find((l) => l.startsWith('data:'))
      if (!line) continue
      try {
        onEvent(JSON.parse(line.slice(5).trim()))
      } catch (e) {
        console.warn('[sse] 无法解析', line)
      }
    }
  }
}

/**
 * App 端 onChunkReceived 返回 ArrayBuffer。同一个流必须复用同一个 decoder，
 * 否则被切开的中文字符会乱码。
 * ⚠️ 待验证：App 端 JS 引擎是否提供 TextDecoder，没有的话需要自写 UTF-8 解码
 */
function createChunkDecoder() {
  const decoder = new TextDecoder('utf-8')
  return (data) => (typeof data === 'string' ? data : decoder.decode(new Uint8Array(data), { stream: true }))
}

/**
 * @param {{message, sessionId?, aiConfigId?, images?}} payload
 * @param {(event: {event: string, data: object}) => void} onEvent
 * @returns {{ abort: () => void, done: Promise<void> }}
 */
export function streamChat(payload, onEvent) {
  const url = `${API_BASE_URL}/ai/chat/stream`
  const headers = { 'Content-Type': 'application/json', ...authHeader() }
  const feed = createSSEParser(onEvent)

  // #ifdef H5
  const controller = new AbortController()
  const done = fetch(url, { method: 'POST', headers, body: JSON.stringify(payload), signal: controller.signal })
    .then(async (res) => {
      if (!res.ok) throw new Error(`请求失败（${res.status}）`)
      const reader = res.body.getReader()
      const decoder = new TextDecoder('utf-8')
      for (;;) {
        const { value, done: finished } = await reader.read()
        if (finished) break
        feed(decoder.decode(value, { stream: true }))
      }
    })
  return { abort: () => controller.abort(), done }
  // #endif

  // #ifndef H5
  let task
  const decodeChunk = createChunkDecoder()
  const appDone = new Promise((resolve, reject) => {
    task = uni.request({
      url,
      method: 'POST',
      header: headers,
      data: payload,
      enableChunked: true,
      responseType: 'arraybuffer',
      success: (res) => (res.statusCode < 400 ? resolve() : reject(new Error(`请求失败（${res.statusCode}）`))),
      fail: reject,
    })
    task.onChunkReceived((res) => feed(decodeChunk(res.data)))
  })
  return { abort: () => task && task.abort(), done: appDone }
  // #endif
}
