# LiteNote（UniApp + Django + MySQL + Docker 重构版）

AI 智能记账应用。参考项目 [GystuG/LiteNote](https://github.com/GystuG/LiteNote)（React Native + NestJS + PostgreSQL），本仓库是按 [`LiteNote技术栈改造方案.md`](./LiteNote技术栈改造方案.md) 重构的骨架。

```
.
├── backend/                 Django 5 + DRF 后端
│   ├── config/              配置（settings/base|dev|prod、urls、asgi）
│   ├── common/              统一响应、异常处理、分页、加密字段、通用 ViewSet
│   ├── apps/
│   │   ├── users/           注册登录、个人资料、头像
│   │   ├── categories/      分类（系统默认 + 自定义）
│   │   ├── accounts/        账户
│   │   ├── bills/           账单 CRUD + 统计
│   │   ├── budgets/         预算 + 进度
│   │   ├── goals/           财务目标
│   │   ├── ai/              AI 模型配置、对话、会话、语音识别
│   │   └── versions/        App 版本检查
│   └── tests/               pytest
├── mobile/                  UniApp（Vue 3 + JavaScript + Pinia + uni-ui）
│   ├── src/api/             接口封装（http.js、index.js、stream.js）
│   ├── src/pages/           页面
│   ├── src/stores/          Pinia
│   ├── src/services/notification/   支付通知解析
│   ├── src/uni_modules/lite-notification-listener/   通知监听 UTS 插件（骨架）
│   └── tests/               解析器单元测试
├── nginx/default.conf       反向代理 + H5 静态资源
├── docker-compose.yml       mysql + backend + nginx
└── .env.example
```

## 快速开始（Docker）

```bash
cp .env.example .env          # 修改其中的密码，并生成 FIELD_ENCRYPTION_KEY
cd mobile && npm install && npm run build:h5 && cd ..
docker compose up -d --build
```

- H5 页面：http://localhost/
- 接口文档：http://localhost/api/docs/
- 管理后台：http://localhost/admin/（先执行 `docker compose exec backend python manage.py createsuperuser`）

首次启动后初始化系统默认分类：用管理员账号调用 `POST /api/categories/init-defaults`，或在 Django shell 中创建。

> 本机 80 端口被占用时，在 `.env` 中设置 `HTTP_PORT=18080` 等其他端口。

## 本地开发

**后端**

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements/dev.txt
.venv/bin/python manage.py migrate      # 未设置 DATABASE_URL 时使用 SQLite
.venv/bin/python manage.py runserver
.venv/bin/pytest                        # 运行测试
```

连接本机 MySQL：在 `backend/.env` 中设置 `DATABASE_URL=mysql://user:pass@127.0.0.1:3306/litenote`。

**移动端**

```bash
cd mobile
npm install
npm run dev:h5      # H5 开发，/api 自动代理到 127.0.0.1:8000
npm test            # 支付通知解析器测试
```

App 端：用 HBuilderX 打开 `mobile/` 目录，运行到 Android 真机。真机无法访问 `127.0.0.1`，需要在 `mobile/.env.development` 中把 `VITE_API_BASE_URL` 设为电脑的局域网地址。通知监听插件需要**自定义基座**才能运行。

## 接口约定

- 所有接口前缀 `/api/`，路径与原 NestJS 项目一致（如 `/api/bills/statistics`）
- 响应统一为 `{ code, message, data, success }`；分页数据为 `{ items, pagination: { page, limit, total, totalPages, hasNext, hasPrev } }`
- JSON 字段和查询参数都使用驼峰（`categoryId`、`startDate`），后端自动转换
- 认证：`Authorization: Bearer <token>`

## 当前进度

| 模块 | 状态 |
|---|---|
| 用户、分类、账户、账单、预算、财务目标 | ✅ 可用，有测试 |
| 统计（汇总、分类占比、日/月趋势） | ✅ 可用，有测试 |
| AI 模型配置（Key 加密存储、设默认、连接测试） | ✅ 可用 |
| AI 会话管理（列表、详情、置顶、软删除） | ✅ 可用 |
| 语音识别 ASR | ✅ 已移植，未用真实接口测试 |
| 流式接口通道（SSE + nginx 不缓冲） | ✅ 通道已验证，对话逻辑待实现 |
| AI 对话（流式 / 非流式、Claude·OpenAI·DeepSeek·Qwen 适配器、工具循环、会话标题与摘要） | ✅ 可用，有测试；未用真实厂商接口验证 |
| AI 账单解析 `parse-bills`（旧接口） | 🚧 TODO |
| UniApp 主干页面（登录、首页、账单、记账、报表） | ✅ 可用 |
| UniApp AI 对话页（流式回复、账单卡片确认保存、历史会话） | ✅ 可用，未在真机验证 |
| 语音输入（按住说话）、拍照 / 相册识别 | ⚠️ 已实现，未在真机 / 浏览器验证；ASR 需配置 `ASR_API_URL` / `ASR_API_KEY` |
| UniApp 预算、财务目标、分类管理（列表 + 新建 / 编辑 / 删除） | ✅ 可用，未在真机验证 |
| UniApp 其他页面（编辑资料、修改密码、检查更新） | 🚧 待实现 |
| 图表（uCharts） | 🚧 报表页暂用进度条代替 |
| 通知监听 UTS 插件 | ⚠️ 骨架，未在 HBuilderX 中编译验证 |

全局搜索 `TODO` 可以找到所有待实现的位置。
