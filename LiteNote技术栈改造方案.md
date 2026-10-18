# LiteNote 技术栈改造方案

> 目标：将开源项目 [LiteNote](https://github.com/GystuG/LiteNote)（AI 智能记账应用）重构为 **UniApp（JavaScript）+ Django + MySQL + Docker**，作为本科毕业设计课题。
>
> 参考代码：`/root/code/Ledger/LiteNote`（commit `78a7197`）

---

## 目录

1. [改造目标与范围](#1-改造目标与范围)
2. [现状分析](#2-现状分析)
3. [目标技术栈](#3-目标技术栈)
4. [目标架构](#4-目标架构)
5. [后端改造：NestJS → Django](#5-后端改造nestjs--django)
6. [数据库改造：PostgreSQL → MySQL](#6-数据库改造postgresql--mysql)
7. [AI 模块改造](#7-ai-模块改造)
8. [移动端改造：React Native → UniApp](#8-移动端改造react-native--uniapp)
9. [支付通知自动记账专项方案](#9-支付通知自动记账专项方案)
10. [Docker 与部署](#10-docker-与部署)
11. [接口兼容与数据迁移](#11-接口兼容与数据迁移)
12. [测试方案](#12-测试方案)
13. [实施计划](#13-实施计划)
14. [风险清单](#14-风险清单)
15. [毕设建议](#15-毕设建议)

---

## 1. 改造目标与范围

### 1.1 目标

| 维度 | 原技术栈 | 目标技术栈 |
|---|---|---|
| 移动端 | React Native 0.81 + TypeScript | UniApp（Vue 3）+ JavaScript |
| 后端 | NestJS 10 + Prisma 6 | Django 5 + Django REST Framework |
| 数据库 | PostgreSQL | MySQL 8 |
| 部署 | Docker（仅后端）+ GitHub Actions + 阿里云 ACR | Docker Compose（后端 + MySQL + Nginx）一键启动 |

### 1.2 功能范围分级

| 级别 | 功能 | 说明 |
|---|---|---|
| **必做（P0）** | 注册登录、账单 CRUD、分类、账户、预算、财务目标、统计报表 | 记账应用的核心 |
| **必做（P0）** | AI 对话记账（含 Tool Calling、会话管理） | 项目最大亮点 |
| **建议做（P1）** | 多模型切换（Claude / OpenAI / DeepSeek / Qwen） | 适配器模式的体现 |
| **建议做（P1）** | 语音记账（ASR）、拍照记账（图片识别） | 依赖 UniApp 录音与相册 API |
| **可选（P2）** | 支付通知自动记账 | 需要自写 UTS 原生插件，见第 9 章 |
| **可选（P2）** | 应用版本检查与更新 | 原项目有 `app-version` 模块 |
| **不建议保留** | 原项目的 RN bsdiff 热更新 | 与 RN 强绑定，UniApp 有自己的 wgt 更新机制 |

---

## 2. 现状分析

### 2.1 后端（`litenote-backend/`）

NestJS 10 模块化单体，源码按业务划分：

```
src/
├── auth/            # JWT 登录注册、改密、资料
├── bills/           # 账单 CRUD + 统计
├── categories/      # 分类
├── accounts/        # 多账户
├── budgets/         # 预算
├── financial-goals/ # 财务目标
├── ai/              # AI 对话 / 工具调用 / ASR（改造重点，约 1500 行）
│   ├── adapters/    # claude / openai / deepseek / qwen 四个适配器 + SSE 解析
│   ├── services/    # chat（747 行）/ session / tool-executor / asr
│   └── tools/       # Tool Calling 定义
├── app-version/     # 应用版本检查
├── hot-update/      # RN 热更新（不迁移）
├── common/          # 统一响应拦截器 / 异常过滤器 / 日志与安全中间件
└── prisma/          # ORM 封装
```

### 2.2 数据模型（`prisma/schema.prisma`）

共 10 个模型：`User`、`AIModelConfig`、`Category`、`Bill`、`Account`、`Budget`、`FinancialGoal`、`AppVersion`、`ChatSession`、`ChatMessage`、`HotUpdate`（其中 `HotUpdate` 不迁移）。

迁移时需要特别处理的字段：

| 字段 | 原类型 | 问题 |
|---|---|---|
| `User.id` | `uuid` | MySQL 无原生 UUID 类型 |
| `Bill.tags` | `String[]` | MySQL 无数组类型 |
| `ChatMessage.toolCalls / toolResult` | `Json` | MySQL 8 支持 JSON，可直接对应 |
| 所有时间戳 | `Timestamptz(6)` | MySQL 无带时区类型，需统一用 UTC 存储 |
| `Bill.amount` 等金额 | `Decimal(15,4)` | MySQL 同样支持，无需改动 |
| `AIModelConfig.apiKey` | `Text`（注释称加密存储） | 需要核对原实现是否真的加密，迁移时补齐 |

### 2.3 移动端（`litenote-mobile-app/`）

React Native 0.81 + TypeScript，约 150 个源文件：

- 页面：`auth`、`dashboard`、`finance`（账单/统计/分类）、`reports`（日月年报表、趋势、资产）、`ai`（聊天/会话列表）、预算、财务目标、设置
- 状态：React Query + MobX + Context Provider
- 原生能力：录音（`react-native-audio-recorder-player`）、图片选择、支付通知监听、热更新
- 图表：`react-native-gifted-charts`、`react-native-svg`

### 2.4 部署

后端已有多阶段 Dockerfile、`docker-compose.yml`，以及 GitHub Actions（构建镜像 → 推送阿里云 ACR → SSH 到 ECS 执行 `docker compose pull && up -d`）。

---

## 3. 目标技术栈

### 3.1 后端

| 用途 | 选型 | 说明 |
|---|---|---|
| 语言 / 框架 | Python 3.12 + Django 5.x | |
| REST 框架 | Django REST Framework (DRF) | 序列化、校验、视图集 |
| 认证 | `djangorestframework-simplejwt` | 对应原 Passport JWT |
| 接口文档 | `drf-spectacular` | 对应原 Swagger |
| 跨域 | `django-cors-headers` | UniApp H5 调试时需要 |
| 数据库驱动 | `mysqlclient`（或纯 Python 的 `PyMySQL`） | 前者性能好但需编译依赖 |
| WSGI/ASGI | `gunicorn` + `uvicorn` worker | 支持流式响应 |
| AI SDK | `anthropic`、`openai` | DeepSeek / Qwen 通过 OpenAI 兼容协议复用 `openai` SDK |
| HTTP 客户端 | `httpx` | 调用 ASR 接口 |
| 配置 | `python-decouple` 或 `django-environ` | 读取 `.env` |
| 测试 | `pytest` + `pytest-django` | |

### 3.2 移动端

| 用途 | 选型 | 说明 |
|---|---|---|
| 框架 | UniApp（Vue 3 + Composition API） | 使用 **JavaScript**（不引入 TypeScript） |
| 构建 | Vite（HBuilderX 或 CLI 工程均可） | 建议 CLI 工程，便于 Git 管理与 CI |
| 状态管理 | Pinia | 替代 MobX + React Query |
| UI 组件库 | uView Plus 或 uni-ui | 二选一，全项目统一 |
| 图表 | uCharts（`qiun-data-charts`） | 替代 gifted-charts |
| 请求封装 | 基于 `uni.request` 自封装，或使用 `alova` | 统一拦截、Token 刷新、错误处理 |
| 原生扩展 | UTS 插件（通知监听） | 见第 9 章 |

> 说明：不使用 TypeScript 会失去类型检查，建议通过 **JSDoc 注释 + ESLint + 接口文档（drf-spectacular）** 来弥补，并在 `src/api/` 下集中管理所有接口函数，避免字段名散落各处。

### 3.3 数据库与基础设施

| 用途 | 选型 |
|---|---|
| 数据库 | MySQL 8.0（`utf8mb4` / `utf8mb4_0900_ai_ci`） |
| 反向代理 / 静态文件 | Nginx |
| 容器编排 | Docker Compose |
| CI/CD（可选） | GitHub Actions |

---

## 4. 目标架构

```
┌────────────────┐        HTTPS         ┌────────────────── Docker Compose ──────────────────┐
│ UniApp 客户端   │ ───────────────────▶ │  nginx                                              │
│ · Android App  │                      │   ├─ /          → H5 静态资源（可选）                 │
│ · H5（调试/演示）│                      │   ├─ /media/    → 用户上传文件                       │
└────────────────┘                      │   └─ /api/      → 反向代理到 backend                 │
                                        │        │                                            │
                                        │        ▼                                            │
                                        │  backend: Django + DRF                              │
                                        │   (gunicorn + uvicorn worker，支持流式响应)           │
                                        │        │                                            │
                                        │        ▼                                            │
                                        │  mysql:8.0 (数据卷持久化)                            │
                                        └─────────────────────────────────────────────────────┘
                                                 │
                                                 ▼ 出站调用
                                    Claude / OpenAI / DeepSeek / Qwen / ASR
```

---

## 5. 后端改造：NestJS → Django

### 5.1 工程结构

```
backend/
├── manage.py
├── config/                 # 项目配置
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── asgi.py
├── apps/
│   ├── users/              # 对应 auth
│   ├── bills/
│   ├── categories/
│   ├── accounts/
│   ├── budgets/
│   ├── goals/              # 对应 financial-goals
│   ├── ai/
│   │   ├── adapters/       # base / claude / openai_compat
│   │   ├── services/       # chat / session / tool_executor / asr
│   │   ├── tools.py
│   │   └── views.py
│   └── versions/           # 对应 app-version
├── common/
│   ├── renderers.py        # 统一响应格式
│   ├── exceptions.py       # 统一异常处理
│   ├── middleware.py       # 请求日志
│   └── pagination.py
├── tests/
├── requirements/
│   ├── base.txt
│   └── dev.txt
├── Dockerfile
└── .env.example
```

### 5.2 组件映射

| NestJS | Django 对应 |
|---|---|
| Module / Controller | Django App + DRF `ViewSet` / `APIView` |
| Service 层 | 保留独立 `services.py`，视图只做参数处理与响应 |
| Prisma schema | `models.py` + Django migrations |
| class-validator DTO | DRF `Serializer` |
| `JwtAuthGuard` / `@Public()` | `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]`，公开接口显式设置 `AllowAny` |
| `@CurrentUser()` | `request.user` |
| `ResponseInterceptor` | 自定义 `Renderer`，保持 `{code, message, data}` 格式 |
| `HttpExceptionFilter` | 自定义 `EXCEPTION_HANDLER` |
| `LoggerMiddleware` / `SecurityMiddleware` | Django Middleware |
| Swagger | `drf-spectacular` |
| `@nestjs/serve-static` | Nginx 提供 `/media/` |
| `ConfigService` | `django-environ` |

### 5.3 关键注意事项

1. **自定义 User 模型必须在第一次 `migrate` 之前确定**。继承 `AbstractBaseUser` + `PermissionsMixin`，保留 `username / email / nickname / avatar / is_active / last_login_at` 字段，主键用 `UUIDField`。
2. **密码哈希兼容**：原项目使用 `bcryptjs`。在 `PASSWORD_HASHERS` 中加入 `django.contrib.auth.hashers.BCryptPasswordHasher`（需安装 `bcrypt`），并保留默认的 PBKDF2。已有用户登录时，Django 会自动识别旧哈希并在登录成功后升级。注意：`bcryptjs` 生成的哈希格式（`$2a$` / `$2b$`）需要在 Django 里加 `bcrypt$` 前缀才能被识别，迁移脚本里需要统一处理。
3. **接口路径与响应格式保持不变**。UniApp 前端按原接口文档开发，对比测试时可以拿同一组请求分别打 NestJS 和 Django，比较响应结构。
4. **流式响应**：AI 对话使用 `StreamingHttpResponse`，运行在 ASGI 模式（`uvicorn` worker）下，避免同步 worker 被长连接占满。
5. **数据隔离**：所有按用户查询的 `ViewSet` 统一在 `get_queryset()` 中过滤 `user=request.user`，避免越权。可以抽一个 `UserOwnedViewSetMixin`。

### 5.4 示例：模型与序列化器（片段）

```python
# apps/bills/models.py
import uuid
from django.conf import settings
from django.db import models

class Bill(models.Model):
    TYPE_CHOICES = [("income", "收入"), ("expense", "支出")]
    SOURCE_CHOICES = [("manual", "手动"), ("voice", "语音"), ("ocr", "拍照"),
                      ("text", "文本"), ("notification", "通知")]

    amount = models.DecimalField(max_digits=15, decimal_places=4)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    time = models.DateTimeField(blank=True, null=True)
    category = models.ForeignKey("categories.Category", null=True, blank=True,
                                 on_delete=models.SET_NULL)
    account = models.ForeignKey("accounts.Account", null=True, blank=True,
                                on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tags = models.JSONField(default=list, blank=True)   # MySQL 无数组类型
    notes = models.TextField(blank=True, null=True)
    receipt_url = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bills"
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "type"]),
            models.Index(fields=["source"]),
        ]
```

---

## 6. 数据库改造：PostgreSQL → MySQL

### 6.1 字段类型映射

| Prisma / PostgreSQL | Django / MySQL | 备注 |
|---|---|---|
| `String @db.Uuid` | `UUIDField`（MySQL 存为 `char(32)`） | 仅 User 使用 UUID，其余表用自增 ID |
| `Int @id @default(autoincrement())` | `AutoField` / `BigAutoField` | |
| `String @db.VarChar(n)` | `CharField(max_length=n)` | |
| `String @db.Text` | `TextField` | |
| `Decimal @db.Decimal(15,4)` | `DecimalField(15, 4)` | |
| `DateTime @db.Timestamptz(6)` | `DateTimeField` | `USE_TZ = True`，库中存 UTC |
| `DateTime @db.Date` | `DateField` | |
| `Boolean` | `BooleanField` | |
| `String[]` | `JSONField(default=list)` | 数据量小，也可拆表 |
| `Json` | `JSONField` | MySQL 5.7+/8 均支持 |

### 6.2 MySQL 特有注意点

- **字符集**：建库时指定 `CHARACTER SET utf8mb4`。分类、账户的 `icon` 字段存 emoji，使用 `utf8` 会乱码。
- **索引长度**：`utf8mb4` 下 `VARCHAR(255)` 唯一索引在老版本可能超限，使用 MySQL 8 默认 InnoDB 无此问题。
- **大小写**：MySQL 默认字符串比较不区分大小写，`username` 唯一性会受影响。注册时统一转小写，或为该列指定 `_bin` 排序规则。
- **JSON 查询**：不要在 `tags` 上做复杂过滤，若要按标签统计，建议拆成 `BillTag` 关联表。
- **统计 SQL**：原项目的统计聚合若使用 Prisma `groupBy`，迁移时用 Django ORM 的 `annotate` + `Sum` + `TruncDate / TruncMonth`。注意 MySQL 的时区函数需要加载时区表（`mysql_tzinfo_to_sql`），建议在应用层统一用 UTC 日期，避免依赖数据库时区转换。
- **事务**：账户余额更新必须在 `transaction.atomic()` 中完成，并使用 `select_for_update()` 防止并发超扣。

### 6.3 Docker 中的 MySQL 配置

```yaml
db:
  image: mysql:8.0
  command: --character-set-server=utf8mb4 --collation-server=utf8mb4_0900_ai_ci
  environment:
    MYSQL_DATABASE: litenote
    MYSQL_USER: litenote
    MYSQL_PASSWORD: ${DB_PASSWORD}
    MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
  volumes:
    - mysql_data:/var/lib/mysql
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    interval: 5s
    timeout: 5s
    retries: 10
```

---

## 7. AI 模块改造

这是后端迁移工作量最大、也最能体现毕设价值的部分。

### 7.1 现有设计（NestJS）

- `AIAdapter` 接口（`base.adapter.ts`）：统一 `parseBills`、`testConnection`、`chat`/流式等方法
- 4 个适配器：Claude（468 行）、OpenAI / DeepSeek / Qwen（共用 `openai-compatible.helper.ts`，387 行）
- `chat.service.ts`（747 行）：对话编排、Tool Calling 循环、SSE 推送、上下文摘要
- `tool-executor.service.ts`：执行 AI 请求的工具（创建/查询/删除/统计账单）
- `session.service.ts`：会话与消息持久化、旧消息摘要压缩
- `asr.service.ts`：调用 Qwen ASR（OpenAI 兼容协议）

### 7.2 Python 实现方案

```
apps/ai/
├── adapters/
│   ├── base.py              # AIAdapter 抽象基类
│   ├── claude.py            # 使用 anthropic SDK
│   ├── openai_compat.py     # 使用 openai SDK，通过 base_url 支持 OpenAI/DeepSeek/Qwen
│   └── factory.py           # 根据 provider 返回适配器
├── services/
│   ├── chat.py              # 对话编排 + Tool Calling 循环
│   ├── session.py           # 会话与消息、摘要压缩
│   ├── tool_executor.py     # 工具执行
│   └── asr.py               # 语音识别
├── tools.py                 # 工具定义（JSON Schema）
└── views.py                 # 流式接口
```

**简化点**：原项目 3 个 OpenAI 兼容厂商有独立适配器文件，Python 里用同一个 `OpenAICompatAdapter`，只通过配置区分 `base_url` 和少量差异（如 Qwen 的视觉模型参数），可以显著减少代码量。

**流式输出**：

```python
# apps/ai/views.py（示意）
from django.http import StreamingHttpResponse

async def chat_stream(request):
    async def event_stream():
        async for event in chat_service.run(request.user, payload):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"   # 让 Nginx 不缓冲
    return resp
```

Nginx 对 `/api/ai/` 路径需要关闭缓冲：`proxy_buffering off;`。

### 7.3 API Key 安全

原 schema 注释写"加密存储"，需要核对原实现。Django 里建议使用 `cryptography.fernet`，密钥来自环境变量 `FIELD_ENCRYPTION_KEY`，对 `AIModelConfig.api_key` 做透明加解密，接口返回时只返回脱敏后的尾 4 位。

### 7.4 可作为毕设评测点

- 四个模型完成同一组"记账指令"的**工具调用准确率**对比
- 对话摘要压缩前后的 **token 消耗**对比
- 首字响应时间（流式 vs 非流式）

---

## 8. 移动端改造：React Native → UniApp

### 8.1 工程结构

```
mobile/
├── src/
│   ├── pages/                   # 对应 RN 的 screens
│   │   ├── auth/                # login / edit-profile / agreement / privacy
│   │   ├── dashboard/
│   │   ├── finance/             # all-bills / bill-detail / create-bill / statistics / category-manage
│   │   ├── reports/             # daily / monthly / yearly / trend / category-analysis / assets
│   │   ├── ai/                  # chat / sessions
│   │   ├── budget/
│   │   ├── goal/
│   │   └── settings/
│   ├── components/              # 对应 RN 的 components（ui / business / charts / forms）
│   ├── api/                     # 对应 services/api，按模块拆文件
│   ├── stores/                  # Pinia
│   ├── utils/                   # format / date / storage / url
│   ├── theme/                   # 主题变量（CSS 变量）
│   ├── uni_modules/             # 自写 UTS 插件放这里
│   ├── App.vue
│   ├── main.js
│   ├── pages.json
│   └── manifest.json
├── package.json
└── vite.config.js
```

### 8.2 技术映射

| React Native | UniApp |
|---|---|
| React Navigation（Tab + Stack） | `pages.json` 配置 `tabBar` 与页面栈，`uni.navigateTo` 跳转 |
| React Query（缓存、重试、失效） | Pinia + 请求层，缓存策略自己实现（列表缓存 + 手动刷新） |
| MobX stores | Pinia stores |
| Context Provider（Auth / Theme / Alert） | Pinia + 全局组件 / `provide/inject` |
| Axios + apisauce | `uni.request` 封装（拦截器、Token、统一错误） |
| AsyncStorage | `uni.setStorageSync / getStorageSync` |
| react-native-gifted-charts / svg | uCharts |
| react-native-audio-recorder-player | `uni.getRecorderManager()` |
| react-native-image-picker | `uni.chooseImage()` / `uni.chooseMedia()` |
| react-native-image-viewing | `uni.previewImage()` |
| react-native-linear-gradient | CSS `linear-gradient` |
| react-native-skeleton-placeholder | uView Plus `u-skeleton` 或自写骨架组件 |
| react-native-sse | 见 8.4 |
| Sentry | 可选，`@sentry/uni-app` 或省略 |
| Reactotron / react-native-config | 移除，用 `import.meta.env` |
| react-native-fs / blob-util / zip-archive | 热更新相关，随热更新一并移除 |

### 8.3 页面迁移优先级

1. **第一批（主干）**：登录、首页 Dashboard、创建账单、账单列表/详情
2. **第二批**：分类管理、账户、预算、财务目标
3. **第三批**：报表（日/月/年视图、趋势、分类分析、资产）— 图表工作量集中在这里
4. **第四批**：AI 对话与会话列表、语音/拍照记账
5. **第五批（可选）**：通知自动记账设置页、版本更新、设置页

### 8.4 AI 流式输出（需先做 PoC）

UniApp 在不同端对流式响应的支持不一致，按优先级尝试：

1. **App 端 `uni.request` + `enableChunked: true`**，通过 `requestTask.onChunkReceived` 逐块接收。需要核实所用 HBuilderX 版本和 Android 基座是否支持。
2. **WebSocket**：后端用 Django Channels 额外提供 WS 端点，兼容性最好，但后端多一套实现。
3. **降级**：不做流式，改为"等待完整回复 + 打字机动画"，体验差一点，但实现最稳。

> 建议在第 1 周用一个最小 Demo 在真机验证方案 1，再决定是否投入方案 2。

### 8.5 样式与主题

原项目有自己的主题系统（`theme/colors.ts`、`spacing.ts`、`typography.ts`，以及 `ThemeProvider`、`BrutalPressable` 等风格化组件）。迁移时把它们转成 `src/theme/variables.scss` 中的 CSS 变量，暗色模式用 `prefers-color-scheme` 或 `uni.onThemeChange` 切换。

---

## 9. 支付通知自动记账专项方案

### 9.1 技术原理

依赖 Android 的 `NotificationListenerService`：用户在系统设置里授予"通知使用权"后，应用能收到其他应用（微信、支付宝等）发出的通知，在 `onNotificationPosted` 中取得包名、标题、正文，再解析金额与商户并创建账单。UniApp 本身不提供此能力，必须写原生扩展。**iOS 无法实现。**

### 9.2 方案对比

| 方案 | 说明 | 优点 | 缺点 |
|---|---|---|---|
| **A. 自写 UTS 插件（推荐）** | 在 `uni_modules` 下写 UTS 插件，Android 端实现通知监听服务 | 免费；HBuilderX 即可开发和云打包；代码自主可控；毕设技术深度更好 | 需要学习 UTS 与 Android Service 基础 |
| B. 购买社区插件 | [Lin-NotificationHandler](https://ext.dcloud.net.cn/plugin?id=19167)，29.98 元，提供通知监听、短信监听、读取活动通知等 | 最快，2~3 天接入 | 闭源；**不支持离线打包**；最近更新为 2024-07-11，新系统兼容性待验证；无微信/支付宝专用解析 |
| C. Android 原生（Java/Kotlin）插件 | 用 Android Studio 开发原生插件 | 可完全控制原生层 | 环境配置重；调试需离线打包；相比 A 无明显收益 |

**结论：采用 A，B 作为兜底，不采用 C。**

### 9.3 UTS 插件设计

```
uni_modules/lite-notification-listener/
├── package.json
├── utssdk/
│   ├── interface.uts               # 对外 API 类型声明
│   └── app-android/
│       ├── index.uts               # 对 JS 暴露的方法
│       ├── NotificationService.kt  # 继承 NotificationListenerService（如 UTS 不能直接定义，则以 Kotlin 源码形式放入）
│       └── AndroidManifest.xml     # 声明 service 与 BIND_NOTIFICATION_LISTENER_SERVICE 权限
```

对外 API（JS 视角）：

```js
import {
  isListenerEnabled,      // 是否已授权
  openListenerSettings,   // 跳转系统"通知使用权"设置页
  startListening,         // 注册回调，参数：包名白名单 + 回调函数
  stopListening,
} from '@/uni_modules/lite-notification-listener'

startListening({ packages: ['com.tencent.mm', 'com.eg.android.AlipayGphone'] }, (n) => {
  // n = { pkg, title, text, postTime }
  const bill = parseNotification(n)          // JS 层解析金额/商户/收支
  if (bill) billStore.createFromNotification(bill)
})
```

### 9.4 解析与记账流程

```
系统通知 → Service.onNotificationPosted → 包名过滤 → 回调到 JS
   → 规则解析（正则，规则表可配置）→ 去重（时间窗口 + 金额 + 商户哈希）
   → 弹窗确认（可选）→ POST /api/bills（source = "notification"）
```

要点：
- 解析规则放在独立文件 `parsers/wechat.js`、`parsers/alipay.js`，每条规则配**测试样例**
- 去重：同一笔支付可能触发多条通知，用"金额 + 商户 + 3 分钟窗口"去重
- App 在后台被杀时服务不工作，需要引导用户关闭电池优化；是否做前台服务保活视工作量决定
- 原项目 `litenote-mobile-app/src/services/paymentNotification/` 中已有解析逻辑，可参照复用其规则（迁移时需细读，本方案编写时未逐行阅读）

### 9.5 验证步骤（第一周完成）

1. 新建 UTS 插件，最小实现：收到任意应用通知后，把包名和标题回调到 JS 并 `console.log`
2. 真机云打包自定义基座，授权通知使用权，验证能收到微信/其他应用的通知
3. **若无法在 UTS 中直接继承 `NotificationListenerService`**，改为在插件目录内放入 Kotlin 源文件；仍不行再切换到方案 B
4. 通过后再做解析与记账

### 9.6 合规说明

此功能仅适用于 Android 个人使用的实验性场景：权限必须用户手动授予；不符合主流应用商店的审核政策；微信、支付宝通知文案会随版本变化。毕设中请明确定位为"可选扩展功能"，核心答辩内容不依赖它。

---

## 10. Docker 与部署

### 10.1 目录结构

```
project/
├── backend/
│   ├── Dockerfile
│   └── ...
├── mobile/                      # UniApp 工程（H5 构建产物可挂到 nginx）
├── nginx/
│   └── default.conf
├── docker-compose.yml
├── docker-compose.dev.yml       # 开发覆盖配置（热重载、暴露端口）
├── .env.example
└── README.md
```

### 10.2 后端 Dockerfile

```dockerfile
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# mysqlclient 的编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .
RUN python manage.py collectstatic --noinput

RUN useradd -m app && chown -R app /app
USER app

EXPOSE 8000
CMD ["gunicorn", "config.asgi:application", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "2", "-b", "0.0.0.0:8000", "--timeout", "120"]
```

> 如需更小镜像，可改为多阶段构建（builder 阶段编译 wheel，运行阶段只装运行时库）。使用纯 Python 的 `PyMySQL` 可以省去 `build-essential`。

### 10.3 docker-compose.yml

```yaml
services:
  db:
    image: mysql:8.0
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_0900_ai_ci
    environment:
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: always

  backend:
    build: ./backend
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - media:/app/media
    command: >
      sh -c "python manage.py migrate --noinput &&
             gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker
             -w 2 -b 0.0.0.0:8000 --timeout 120"
    restart: always

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - media:/var/www/media:ro
      - ./mobile/dist/build/h5:/usr/share/nginx/html:ro   # 可选：H5 版本
    depends_on:
      - backend
    restart: always

volumes:
  mysql_data:
  media:
```

### 10.4 Nginx 关键配置

```nginx
server {
    listen 80;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 20m;          # 图片/音频上传
    }

    # AI 流式接口：关闭缓冲
    location /api/ai/ {
        proxy_pass http://backend:8000;
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
    }

    location /media/ { alias /var/www/media/; }
    location /       { try_files $uri $uri/ /index.html; }
}
```

### 10.5 环境变量（`.env.example`）

```
# Django
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL
DB_NAME=litenote
DB_USER=litenote
DB_PASSWORD=change-me
DB_ROOT_PASSWORD=change-me
DB_HOST=db
DB_PORT=3306

# 加密 AI Key 的密钥（Fernet，32 字节 base64）
FIELD_ENCRYPTION_KEY=

# ASR（兼容 OpenAI 协议）
ASR_API_URL=
ASR_API_KEY=
ASR_MODEL=qwen3-asr-flash
```

### 10.6 CI/CD（可选）

保留原 GitHub Actions 思路：`push → 构建镜像 → 推送镜像仓库 → SSH 到服务器 compose pull && up -d`。只需要调整构建上下文为 `backend/` 和镜像名。毕设演示阶段只需要本地 `docker compose up -d`，不必真的部署到云上；若部署，请更换原项目 workflow 中的 secrets，不要沿用原作者的仓库配置。

### 10.7 移动端打包

移动端不在 Docker 中打包 App。流程：HBuilderX（或 CLI + HBuilderX 云打包）生成 Android APK/AAB；H5 版本用 `npm run build:h5` 输出到 `dist/build/h5`，挂载到 Nginx 即可。

---

## 11. 接口兼容与数据迁移

### 11.1 接口契约

- 以原项目 Swagger 为基准，导出 OpenAPI JSON，作为 Django 实现的验收标准
- 保持：路径、HTTP 方法、字段名（原项目前端用驼峰如 `categoryId`，DRF 默认下划线，需要 `djangorestframework-camel-case` 或在序列化器中显式指定 `source`）、统一响应格式
- 统一响应格式沿用 `{ code, message, data }`

### 11.2 数据迁移（仅在需要保留旧数据时）

演示项目通常不需要。如果需要：

1. 从 PostgreSQL 导出各表为 CSV 或 JSON
2. 编写一次性 Django management command 导入 MySQL
3. 注意：UUID 保持原值；`tags` 数组转 JSON 列表；时间戳统一转 UTC；bcrypt 哈希按 5.3 的方式补前缀
4. 导入后核对每张表行数与金额汇总

---

## 12. 测试方案

| 层级 | 工具 | 内容 |
|---|---|---|
| 后端单元测试 | pytest + pytest-django | 模型约束、序列化器校验、统计聚合、工具执行器 |
| 后端接口测试 | DRF `APIClient` | 每个接口的认证、越权、参数校验、响应格式 |
| AI 适配器测试 | mock SDK 响应 | 工具调用循环、流式事件拼装、异常重试 |
| 契约对比 | 脚本 | 同一组请求分别打旧 NestJS 与新 Django，对比 JSON 结构 |
| 前端 | 手工测试清单 + 关键工具函数的单测（Vitest） | UniApp 页面自动化成本高，核心流程用测试用例表覆盖 |
| 部署验收 | `docker compose up` 全新环境 | 从零启动到完成一笔账单的端到端流程 |

---

## 13. 实施计划

按 12 周安排（可根据学生基础压缩或延长）：

| 周次 | 阶段 | 任务 | 交付物 |
|---|---|---|---|
| 1 | 调研与 PoC | 通读原项目；UniApp 流式请求 PoC；UTS 通知监听 PoC；确定功能范围 | 可行性验证记录、功能清单 |
| 2 | 后端骨架 | Django 工程、自定义 User、JWT、统一响应、Docker + MySQL 跑通 | `docker compose up` 可访问 Swagger |
| 3–4 | 后端核心业务 | 账单、分类、账户、预算、财务目标、统计接口 + 测试 | 接口通过契约对比 |
| 5–6 | 后端 AI 模块 | 适配器、Tool Calling、会话与摘要、流式接口、ASR | 四个模型均可完成对话记账 |
| 7 | 前端骨架与主干页面 | 工程搭建、请求层、Pinia、登录、首页、记账、账单列表 | 真机可登录记账 |
| 8–9 | 前端业务页面 | 分类/账户/预算/目标、报表与图表 | 报表页面完成 |
| 10 | 前端 AI 与多媒体 | AI 对话、会话列表、语音/拍照记账 | AI 记账全流程跑通 |
| 11 | 可选扩展与联调 | 通知自动记账（UTS）、版本更新、整体联调 | 扩展功能可演示 |
| 12 | 收尾 | 测试补全、文档、论文数据整理、演示环境 | 毕设材料 |

---

## 14. 风险清单

| 风险 | 影响 | 应对 |
|---|---|---|
| UniApp 流式请求在真机不稳定 | AI 对话体验下降 | 第 1 周 PoC；备选 WebSocket；最终降级为非流式 |
| UTS 无法直接实现通知监听服务 | 通知记账受阻 | 在插件内混入 Kotlin 源码；仍不行则购买 Lin-NotificationHandler；或降级为可选功能 |
| 学生 Python/Django 经验不足 | 后端进度延迟 | 第 1 周安排 Django 入门；AI 适配器只做 Claude + OpenAI 兼容两类 |
| 前端不用 TypeScript，字段错误难发现 | 联调反复 | 接口集中封装 + JSDoc；用 Swagger 对字段；加 ESLint |
| bcrypt 哈希迁移格式不对 | 老用户无法登录 | 仅在需要保留旧数据时处理；先在测试库验证 |
| MySQL 时区与聚合统计 | 日/月统计边界错误 | 统一 UTC 存储，统计按用户时区在应用层处理，并为月末、跨年写测试 |
| 第三方 AI 接口费用与网络 | 开发测试受阻 | 开发期优先用国内兼容接口（DeepSeek / Qwen）；对话测试用 mock |
| API Key 泄露 | 安全问题 | 密钥只放 `.env`，不提交；`.env.example` 不含真实值；返回接口脱敏 |
| 通知监听功能的合规问题 | 答辩被质疑 | 明确定位为个人使用的实验功能，不在核心范围 |

---

## 15. 毕设建议

1. **范围优先级**：先保证 P0 + P1 完整可演示，P2 视进度而定。宁可少一个功能，也要保证 Docker 一键启动、文档完整、测试可复现。
2. **论文可展开的章节**：
   - 技术选型对比（RN vs UniApp，NestJS vs Django，PostgreSQL vs MySQL）
   - 适配器模式在多模型接入中的应用
   - Tool Calling 驱动的自然语言记账设计
   - 对话上下文摘要压缩策略
   - 容器化部署与环境一致性
   - 迁移前后的接口响应时间、包体积、开发工作量对比
3. **考核点**：不要只做"翻译式迁移"，建议要求学生在迁移之外至少完成一项有独立思考的改进（例如统一错误码体系、API Key 加密存储、统计查询优化、AI 评测实验）。
4. **原项目许可**：开始前确认 LiteNote 仓库的开源许可证（本方案编写时未核对），在论文和代码中注明参考来源，避免学术诚信问题。
5. **前置知识准备**：Vue 3 基础、Django + DRF 基础、Docker 基础，建议在第 1 周内完成入门。

---

## 附录：本方案中尚未验证的事项

以下内容为基于文档和经验的判断，**实施前需要用最小 Demo 验证**：

- UTS 中能否直接定义继承 `NotificationListenerService` 的类，或是否需要混入 Kotlin 源码
- UniApp App 端 `enableChunked` 流式接收在目标基座版本上的稳定性
- Lin-NotificationHandler 在 Android 15 及以上系统的可用性
- 原项目 API Key 是否真的加密存储
- 原项目接口字段命名风格（驼峰或下划线）及统一响应结构的具体字段
- LiteNote 的开源许可证类型
