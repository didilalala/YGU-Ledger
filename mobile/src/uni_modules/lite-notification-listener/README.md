# lite-notification-listener

监听其他应用（微信、支付宝）的通知，供支付通知自动记账使用。仅 Android。

## 当前状态

**未编译、未在真机运行。** 代码已对照 DCloud 官方文档核对过语法，但文档没有 NotificationListenerService 的 UTS 示例，能否编译通过要以 HBuilderX 为准。

### 已被官方文档确认
| 点 | 依据 |
|---|---|
| UTS 类可以 `extends` 原生类，需要显式 `constructor(){ super() }`，重写用 `override`、参数可空 | uts-for-android 文档中的 `BroadcastReceiver`、`Thread` 示例 |
| Service 在插件的 `AndroidManifest.xml` 里注册 | 文档示例 `<service android:name="uts.sdk.modules.utsNativepage.ForeService"/>` |
| 类名规则 `uts.sdk.modules.<插件ID转驼峰>.<类名>` | 同上；本插件 `lite-notification-listener` → `liteNotificationListener` |
| 修改清单必须**自定义基座**，原生配置变更要云打包后才生效 | uts-plugin 文档 |
| 可以混编 `hybrid.kt`（HBuilderX 4.25+） | uts-plugin 文档 |

### 待真机验证
1. UTS 里继承 `NotificationListenerService` 能否编译通过（不行就改 `hybrid.kt`，见下）。
2. 清单里的 service 类名与编译产物是否一致（以云打包后 APK 中的实际类名为准）。
3. 回调里传给 JS 的 `NotificationInfo` 对象，在 JS 侧字段是否可直接读取（`info.pkg`、`info.text`）。
4. `UTSAndroid` 在 uni-app（非 uni-app x）项目里是否需要显式 `import`（代码里已加）。
5. 回调在主线程触发：这是按 Android 框架行为推断的（`NotificationListenerService` 的回调走主线程 Handler），不是文档结论。
6. **后台存活**：应用被系统杀掉后，JS 回调不存在，通知会漏记。本插件不处理这个问题，只能靠用户允许后台运行。

## 验证步骤

1. HBuilderX（4.25 以上）打开 `mobile/`，菜单：运行 → 运行到手机或模拟器 → **制作自定义调试基座**，等待云打包完成。
2. 运行到真机（自定义基座），进入「我的 → 通知自动记账」。
3. 页面显示"通知使用权：未开启"→ 点"去开启"，在系统设置里给 LiteNote 授权，回到应用应显示"已开启"。
   - 这一步验证 `isListenerEnabled` / `openListenerSettings`，也验证 service 已被系统识别（授权列表里能看到 LiteNote）。
4. 打开"自动记账"开关。
5. **不依赖微信的最小测试**：开发模式下页面会多出"原始通知（调试）"一栏，此时不过滤包名。用 adb 发一条测试通知：
   ```bash
   adb shell cmd notification post -S bigtext -t "微信支付" test "微信支付：向星巴克支付 ¥32.00"
   ```
   "原始通知"里应出现 `[com.android.shell] 微信支付 | 微信支付：向星巴克支付 ¥32.00`。这一条出现，就证明 Service 注册、授权、回调到 JS 整条链路是通的。
   （这条测试通知的包名不是微信，解析器会忽略它，所以不会生成账单；解析器本身由 `npm test` 覆盖。）
6. 用微信、支付宝各真实付一笔小额款项，从"原始通知"里抄下真实的包名和文本，回填到 `src/services/notification/parser.js` 的正则和 `tests/parser.test.js`。

## 如果 UTS 继承编译失败：改用 hybrid.kt

把服务类写成 `utssdk/app-android/hybrid.kt`，用 Kotlin 继承 `NotificationListenerService`，在里面保存一个静态回调；`index.uts` 只负责调用 Kotlin 的静态方法（`startListening` / `stopListening`）。清单里的类名改为 Kotlin 类的完整包名。官方文档页面里没有 `hybrid.kt` 的调用示例，需要参考 DCloud「UTS 混编」文档。
