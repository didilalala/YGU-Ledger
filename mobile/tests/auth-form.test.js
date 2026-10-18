import test from 'node:test'
import assert from 'node:assert/strict'
import { validateAuthForm } from '../src/utils/auth-form.js'

test('登录：只要求非空', () => {
  assert.deepEqual(validateAuthForm('login', { username: 'ab', password: '1' }), {})
  assert.deepEqual(validateAuthForm('login', { username: '  ', password: '' }), { username: '请输入用户名', password: '请输入密码' })
})

test('注册：用户名 ≥3、密码 ≥6、两次一致', () => {
  assert.deepEqual(validateAuthForm('register', { username: 'abc', password: '123456', confirmPassword: '123456' }), {})
  assert.equal(validateAuthForm('register', { username: 'ab', password: '123456', confirmPassword: '123456' }).username, '用户名至少 3 位')
  assert.equal(validateAuthForm('register', { username: 'abc', password: '123', confirmPassword: '123' }).password, '密码至少 6 位')
  assert.equal(validateAuthForm('register', { username: 'abc', password: '123456', confirmPassword: '654321' }).confirmPassword, '两次输入的密码不一致')
})

test('用户名两端的空格不计入长度', () => {
  assert.equal(validateAuthForm('register', { username: ' ab ', password: '123456', confirmPassword: '123456' }).username, '用户名至少 3 位')
})
