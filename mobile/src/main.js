import { createSSRApp } from 'vue'
import * as Pinia from 'pinia'
import App from './App.vue'
import { setupRouteGuard } from './utils/route-guard'

export function createApp() {
  const app = createSSRApp(App)
  app.use(Pinia.createPinia())
  setupRouteGuard()
  return {
    app,
    Pinia, // App 端使用 Pinia 需要导出
  }
}
