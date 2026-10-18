/**
 * 图片与文件处理。App 端用 plus.io / uni.compressImage，H5 端用 FileReader / canvas。
 * ⚠️ 两端都未在真机或浏览器里验证过，见 README 的"未验证"说明。
 */

export const MAX_IMAGE_SIDE = 1024
export const IMAGE_QUALITY = 0.8

/** 等比缩小到最长边不超过 max；本来就不超过时原样返回（不放大） */
export function fitSize(width, height, max = MAX_IMAGE_SIDE) {
  const longest = Math.max(width, height)
  if (!longest || longest <= max) return { width, height }
  const scale = max / longest
  return { width: Math.round(width * scale), height: Math.round(height * scale) }
}

/** "data:audio/aac;base64,xxxx" → "xxxx"；已经是纯 Base64 时原样返回 */
export function stripDataUrl(value) {
  const i = value.indexOf(';base64,')
  return value.startsWith('data:') && i !== -1 ? value.slice(i + 8) : value
}

/** 本地文件路径 → data URL */
export function fileToDataUrl(path) {
  return new Promise((resolve, reject) => {
    // #ifdef APP-PLUS
    plus.io.resolveLocalFileSystemURL(
      path,
      (entry) => entry.file((file) => {
        const reader = new plus.io.FileReader()
        reader.onloadend = (e) => resolve(e.target.result)
        reader.onerror = () => reject(new Error('读取文件失败'))
        reader.readAsDataURL(file)
      }, reject),
      reject,
    )
    // #endif
    // #ifdef H5
    fetch(path)
      .then((res) => res.blob())
      .then((blob) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = () => reject(new Error('读取文件失败'))
        reader.readAsDataURL(blob)
      })
      .catch(reject)
    // #endif
  })
}

const getImageInfo = (src) =>
  new Promise((resolve, reject) => uni.getImageInfo({ src, success: resolve, fail: reject }))

/** 压缩成最长边 1024 的 JPEG，返回 data URL */
async function compressToDataUrl(path) {
  const info = await getImageInfo(path)
  const size = fitSize(info.width, info.height)

  // #ifdef APP-PLUS
  const resized = size.width !== info.width
  const { tempFilePath } = await new Promise((resolve, reject) =>
    uni.compressImage({
      src: path,
      quality: Math.round(IMAGE_QUALITY * 100),
      // 只在需要缩小时才传尺寸，避免小图被放大
      ...(resized ? { compressedWidth: size.width, compressedHeight: size.height } : {}),
      success: resolve,
      fail: reject,
    }),
  )
  return fileToDataUrl(tempFilePath)
  // #endif

  // #ifdef H5
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = size.width
      canvas.height = size.height
      canvas.getContext('2d').drawImage(img, 0, 0, size.width, size.height)
      resolve(canvas.toDataURL('image/jpeg', IMAGE_QUALITY))
    }
    img.onerror = () => reject(new Error('无法读取图片'))
    img.src = path
  })
  // #endif
}

/**
 * 拍照或从相册选图，返回压缩后的 data URL 数组；用户取消返回空数组。
 * @param {'camera'|'album'} source
 * @param {number} count 最多还能选几张
 */
export async function pickImages(source, count = 1) {
  let paths
  try {
    const res = await uni.chooseImage({
      count: source === 'camera' ? 1 : count,
      sizeType: ['compressed'],
      sourceType: [source],
    })
    paths = res.tempFilePaths
  } catch (e) {
    return [] // 取消选择
  }
  return Promise.all(paths.map(compressToDataUrl))
}
