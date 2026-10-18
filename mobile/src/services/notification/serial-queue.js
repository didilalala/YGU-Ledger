/**
 * 串行队列：同一时间只处理一个任务。
 * 连续来几条支付通知时，确认弹窗要一个接一个弹，不能叠在一起；某个任务失败也不能卡住后面的。
 */
export function createSerialQueue() {
  let tail = Promise.resolve()
  let pending = 0
  return {
    /** 加入队列，返回该任务自己的结果（失败时 reject，但不影响后续任务） */
    push(task) {
      pending++
      const run = tail.then(task)
      // 计数的回调先于调用方的 then 登记，所以调用方拿到结果时 size 已经更新
      const done = () => { pending-- }
      run.then(done, done)
      tail = run.catch(() => {})
      return run
    },
    get size() {
      return pending
    },
  }
}
