/**
 * 登录 / 注册表单校验（纯函数）。返回 { 字段名: 错误文案 }，空对象表示通过。
 * 规则与后端 RegisterSerializer 一致：用户名至少 3 位，密码至少 6 位。
 */
export function validateAuthForm(mode, { username = '', password = '', confirmPassword = '' }) {
  const errors = {}
  const name = username.trim()
  if (!name) errors.username = '请输入用户名'
  else if (mode === 'register' && name.length < 3) errors.username = '用户名至少 3 位'

  if (!password) errors.password = '请输入密码'
  else if (mode === 'register' && password.length < 6) errors.password = '密码至少 6 位'

  if (mode === 'register' && !errors.password && password !== confirmPassword) {
    errors.confirmPassword = '两次输入的密码不一致'
  }
  return errors
}
