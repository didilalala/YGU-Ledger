/**
 * 录音。App 端用 uni.getRecorderManager，H5 端用 MediaRecorder（需要 HTTPS 或 localhost）。
 * 一次录音的生命周期：start() → stop() 得到音频 / cancel() 丢弃。
 * ⚠️ 未在真机或浏览器里验证过。
 */
import { fileToDataUrl, stripDataUrl } from './media.js'

/** 录音最短时长，更短的视为误触 */
export const MIN_DURATION_MS = 500
/** 录音最长时长 */
export const MAX_DURATION_MS = 60000

/** "audio/webm;codecs=opus" → "audio/webm" */
export const baseMime = (mime) => (mime || '').split(';')[0]

/**
 * @returns {{
 *   start: () => Promise<void>,
 *   stop: () => Promise<{base64: string, mimeType: string, duration: number} | null>,
 *   cancel: () => void,
 * }}
 */
export function createRecorder() {
  let startedAt = 0
  let starting = null // start() 还没完成时，stop() 要等它（用户可能一按即放）
  let impl = null

  async function begin() {
    // #ifdef APP-PLUS
    impl = appRecorder()
    // #endif
    // #ifdef H5
    impl = await h5Recorder()
    // #endif
    await impl.start()
    startedAt = Date.now()
  }

  return {
    start() {
      starting = begin()
      return starting
    },
    async stop() {
      if (!starting) return null
      try {
        await starting
      } catch (e) {
        starting = null
        throw e
      }
      starting = null
      const duration = Date.now() - startedAt
      const result = await impl.stop()
      return duration < MIN_DURATION_MS ? null : { ...result, duration }
    },
    cancel() {
      const pending = starting
      starting = null
      pending?.then(() => impl.cancel()).catch(() => {})
    },
  }
}

// #ifdef APP-PLUS
function appRecorder() {
  const manager = uni.getRecorderManager()
  let settle = null
  manager.onStop((res) => settle?.resolve(res.tempFilePath))
  manager.onError((err) => settle?.reject(new Error(err.errMsg || '录音失败')))
  return {
    start: () => {
      manager.start({ format: 'aac', sampleRate: 16000, numberOfChannels: 1, encodeBitRate: 48000, duration: MAX_DURATION_MS })
      return Promise.resolve()
    },
    async stop() {
      const path = await new Promise((resolve, reject) => {
        settle = { resolve, reject }
        manager.stop()
      })
      return { base64: stripDataUrl(await fileToDataUrl(path)), mimeType: 'audio/aac' }
    },
    cancel() {
      settle = null
      manager.stop()
    },
  }
}
// #endif

// #ifdef H5
async function h5Recorder() {
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
    throw new Error('当前浏览器不支持录音（需要 HTTPS 或 localhost）')
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'].find((m) => MediaRecorder.isTypeSupported(m))
  const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined)
  const chunks = []
  recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data)
  const release = () => stream.getTracks().forEach((t) => t.stop())
  return {
    start: () => recorder.start(),
    stop: () =>
      new Promise((resolve, reject) => {
        recorder.onstop = async () => {
          release()
          try {
            const blob = new Blob(chunks, { type: recorder.mimeType })
            resolve({ base64: stripDataUrl(await fileToDataUrl(URL.createObjectURL(blob))), mimeType: baseMime(recorder.mimeType) })
          } catch (e) {
            reject(e)
          }
        }
        recorder.stop()
      }),
    cancel() {
      recorder.onstop = release
      recorder.stop()
    },
  }
}
// #endif
