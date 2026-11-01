# FeedLine 原生 Android 与 Compose 源码学习指南

核对日期：2026-11-01。源码为公开仓库 `hejulian2004/testDemo` 的 `main`，固定提交 `8aa963a945176f8d5903b0b706423fd95cc011ff`。该仓库 README 明确描述 Compose FeedLine 信息流作业，代码包含对应的信息流、通知和发布页面。

这份指南补充原面试手册 C01—C48：原手册查概念，本篇把概念落到真实代码、失效场景和可完成的练习。文中的“源码事实”来自这一提交的静态阅读；“改进建议”和“练习”不是已实现成果。本次未编译 APK、未执行真机或性能测试，也未修改 FeedLine 源码。代码能力不能直接当作个人独立设计贡献。

## 阅读顺序

1. 先读第1节，校正项目目前实际做到了什么。
2. 沿第2节刷新、第6节点赞、第9节媒体发布三条链路，在 IDE 中逐个跳转。
3. 重点学习生命周期、Compose 状态、协程与数据库边界。
4. 选第14节的两个实验亲手完成，再用自己的结果回答第13节面试题。

## 1 先建立准确的项目地图

### 1.1 版本与实现以代码为准

| 项目 | 本次看到的声明或实现 | 面试中的边界 |
| --- | --- | --- |
| Android | minSdk 24，targetSdk 36，compileSdk 36 且配置 minor API 1 | 这是声明，不代表所有系统与设备都验证过 |
| 构建 | AGP 9.2.1，Kotlin Compose 插件 2.2.10 | 不等于已验证本地构建环境一致 |
| Compose | BOM 2026.02.01，另有 UI 1.11.4、Material3 1.4.0 等显式版本 | BOM 与显式依赖混用，最终版本需看 Gradle 解析结果 |
| 图片 | Coil 3.0.4 | 不能套用 Coil 2 的包名和所有行为细节 |
| HTTP | Retrofit 2.9.0，Gson converter；配置为占位域名 | 网络失败会回退缓存或演示数据；点赞、评论、发布当前主要是本地行为 |
| 本地存储 | SQLiteOpenHelper + Gson，数据库版本3 | README 写 Room，但当前 app 代码不是 Room；版本目录有别名不代表使用 |
| 状态 | ViewModel、StateFlow、默认 MutableSharedFlow | 当前 UI 使用 collectAsState，不是 collectAsStateWithLifecycle |
| 页面切换 | FeedUiState.currentScreen 枚举加条件分支 | 当前不是 Navigation Compose 的 NavHost/back stack |
| 视频 | AndroidView 包装 VideoView，MediaMetadataRetriever 提取封面 | 当前不是 Media3、ExoPlayer 或 CameraX |
| 埋点 | AnalyticsTracker 接口，Log + Toast 实现 | 不能说已接真实分析平台、建立生产数据闭环 |

源码：[app/build.gradle.kts](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/build.gradle.kts)；[gradle/libs.versions.toml](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/gradle/libs.versions.toml)；[data/database/LocalDatabaseHelper.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/database/LocalDatabaseHelper.kt)；[presentation/FeedScreen.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/FeedScreen.kt)；[presentation/components/FeedPostItem.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/components/FeedPostItem.kt)；[data/analytics/LogAnalyticsTracker.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/analytics/LogAnalyticsTracker.kt)。

本篇查阅了 Android/Kotlin 当前官方文档解释原理。**官方文档描述的推荐方式不自动等于项目已经采用的方式。** 新 API 能否直接使用，仍须核对项目依赖、编译器配置和目标设备。文档中的库版本也不替代项目的 Gradle dependencyInsight 结果。

### 1.2 四个层次各自负责什么

```text
MainActivity / setContent
    └─ FeedScreen 与组件：显示状态、收集交互、平台媒体入口
         └─ FeedViewModel：Intent 分发、UiState、Effect
              └─ UseCase：一个动作或跨仓储动作的组合
                   └─ FeedRepository 接口
                        └─ FeedRepositoryImpl
                             ├─ MutableStateFlow 内存状态
                             ├─ Retrofit 刷新接口
                             └─ LocalDatabaseHelper / SQLite / Gson
```

MainActivity 用 ViewModel factory 提供 Repository 和当前用户。这里是手动依赖构造，不是 Hilt。`RefreshFeedUseCase` 只是委托，`LikePostUseCase` 还组合了点赞与通知逻辑。这有助于隔离 UI，但不是每个一行 UseCase 都自动带来很大架构价值；能否独立测试、业务是否真的变化更重要。

源码：[MainActivity.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/MainActivity.kt)；[presentation/FeedViewModel.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/FeedViewModel.kt)；[domain/usecase/RefreshFeedUseCase.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/domain/usecase/RefreshFeedUseCase.kt)；[domain/usecase/LikePostUseCase.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/domain/usecase/LikePostUseCase.kt)。

## 2 先走通一次真实刷新

### 2.1 当前执行顺序

1. MainActivity 创建 FeedRepositoryImpl，构造器 `init` 同步读取帖子与通知缓存。
2. FeedViewModel 初始化时启动 `observeFeeds()`、`observeNotifications()`，并调用 `refreshFeed(false)`。
3. 用户下拉刷新时，FeedScreen 发出 `FeedIntent.Refresh`，进入名称为 `handelIntent` 的方法。这个拼写就是当前源码名称。
4. ViewModel 在 `viewModelScope.launch` 中把 `isLoading` 置为 true，然后调用 RefreshFeedUseCase。
5. Repository 的 `refreshFeed()` 先 `delay(1000.milliseconds)`，再调用 Retrofit `getFeedPosts()`。
6. 返回非 null 列表时，先删本地帖子，再批量插入，并更新 `_feedPosts`；失败时读缓存，缓存为空时生成演示数据。
7. `getFeedPosts()` 将帖子按创建时间排序；ViewModel 收到列表后更新 UiState。
8. UI 用 `collectAsState()` 读取新状态；手动刷新完成时还通过 SharedFlow 发送“刷新成功”或“刷新失败”。

源码：[presentation/FeedScreen.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/FeedScreen.kt)；[presentation/FeedViewModel.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/FeedViewModel.kt)；[data/FeedRepositoryImpl.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/FeedRepositoryImpl.kt)；[data/network/FeedApiService.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/network/FeedApiService.kt)。

### 2.2 必须能说清的三个问题

**“为什么失败后还能看到帖子？”** 当前有缓存回退和假数据回退。Retrofit 配置使用占位域名，因此这份代码不能作为真实后端联调成功的证据。看到列表不代表网络成功，也不代表离线同步完成。源码：[data/network/RetrofitClient.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/network/RetrofitClient.kt)。

**“为什么网络失败仍可能显示刷新成功？”** Repository 捕获网络异常并完成缓存/演示数据回退，没有把“数据来自哪里”作为结果返回。ViewModel 只看 UseCase 是否抛出异常。因此它的“成功”更接近“这个函数正常返回”，不等于“远端刷新成功”。

**“delay 一秒是不是后台线程睡了一秒？”** `delay` 挂起协程，不把线程堵住；但之后的普通读库、Gson 解析等仍可能执行在调用者线程。人为延时是演示行为，不是性能优化，也不能当成网络真实耗时。

**建议而非现状：** 让 Repository 返回明确结果，例如 `RemoteUpdated`、`CacheFallback`、`Empty`、`Failed`，并让 UI 按结果显示提示；演示数据入口与生产回退分开。若同时允许多次刷新，要指定“拒绝重复、取消前次、串行执行、只接收最新结果”中的一种策略，而不是交给时序碰运气。

### 2.3 刷新状态还存在一个值得验证的时序

`observeFeeds()` 收到任何帖子列表都会将 `isLoading=false`。启动时缓存或空列表可能先到，而网络刷新仍在进行。一个布尔值同时表达“有无首屏内容”和“网络请求是否运行”，容易产生语义冲突。UiState 虽定义 `isRefreshing`，当前主要逻辑仍围绕 `isLoading`。

练习：用可控制完成时间的 fake Repository，让缓存先返回、网络晚返回，记录 loading 的所有状态变化。改进时可区分首屏加载、后台刷新和已有内容，不能只在一个位置多写一次 true。

## 3 Activity 生命周期和状态恢复

### 3.1 原生 Android 为什么必须理解宿主生命周期

Activity 的创建、启动、恢复、暂停、停止、销毁描述的是组件状态；进程能否存活由系统整体管理。Compose 替换了 UI 描述方式，没有取消 Activity、Window、主线程和进程限制。

FeedLine 目前只有一个 Activity。旋转等配置变化通常重建 Activity，但相同 owner 的 ViewModel 可保留；系统回收进程后，原 ViewModel、Repository 和协程都不存在。`onDestroy` 不是可靠的最后保存机会。官方原理：[Activity 生命周期](https://developer.android.com/guide/components/activities/activity-lifecycle)、[ViewModel](https://developer.android.com/topic/libraries/architecture/viewmodel)。

### 3.2 用本项目区分四种状态

| 状态 | 当前例子 | 应该考虑的恢复策略 |
| --- | --- | --- |
| 短暂界面状态 | 底部弹窗是否展开、预览是否打开 | 可在重建后关闭，也可保存少量键值，先定产品要求 |
| 用户尚未提交的输入 | 发布页文字、评论输入、选中的媒体 | rememberSaveable / SavedStateHandle 保存小状态；重要草稿持久化 |
| 可重新查询的数据 | 帖子列表、通知列表 | 保存必要 ID，从数据库或网络重建，不把整批数据塞 Bundle |
| 正在执行的任务 | 发布复制文件、刷新请求 | 明确作用域、取消和恢复语义，不能只恢复一个“进行中”布尔值 |

源码中发布文字、选中媒体、评论内容大多使用普通 `remember`；UiState 的页面枚举只存在 ViewModel 内。当前没有看到 SavedStateHandle 或完整草稿持久化流程。不要回答“旋转和杀进程都能自动恢复”。源码：[presentation/FeedScreen.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/FeedScreen.kt)；[presentation/components/PublishScreen.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/components/PublishScreen.kt)；[presentation/FeedViewModel.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/FeedViewModel.kt)。

`rememberSaveable` 和 SavedStateHandle 适合可保存的小型状态，不是任意对象仓库。恢复依赖系统保存状态流程，不是用户清数据、所有强制结束或重启场景的永久存储承诺。官方：[Compose 保存 UI 状态](https://developer.android.com/develop/ui/compose/state-saving)。

### 3.3 面试常问的 Context 泄漏

本项目 BaseApplication 保存的是 `applicationContext`，不是 Activity，所以不能仅凭 static Context 判定它泄漏 Activity。真正要追的是：长生命周期 Repository、静态缓存或未完成回调是否持有短生命周期 Activity/View。

反过来，Application Context 也不能替代所有 UI Context，例如窗口、主题和某些交互依赖当前宿主。不要把“换成 Application Context”作为所有内存问题的统一修复。源码：[BaseApplication.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/BaseApplication.kt)。

## 4 Compose 怎样把状态变化变成界面变化

### 4.1 三个阶段与依赖读取

Compose 一帧可涉及组合、布局、绘制。组合决定 UI 结构；布局确定尺寸与位置；绘制产生可见内容。状态被哪个阶段读取，影响它变化时需要重做哪些工作。重组不是整页重绘，也不是所有函数都无条件重新执行。官方：[Compose phases](https://developer.android.com/develop/ui/compose/phases)。

FeedLine 的 UiState 由 StateFlow 收集为 Compose State，组件读取其中帖子和加载状态。`FeedPost` 使用 val 属性，点赞时用 `copy` 加新列表，减少了原地修改对象后 UI 无法观察的风险。但 `List` 是只读接口，不保证底层对象永远不可变。

Snapshot 系统记录 Compose 可观察 State 的读写；普通可变集合内部的每次变化不会自动成为 Snapshot 变化。不能认为给变量加 `remember` 就让对象内部所有字段变成可观察。官方：[Compose State](https://developer.android.com/develop/ui/compose/state)。

### 4.2 stable key 与稳定性分别解决什么

FeedScreen 的 `LazyColumn.items` 使用 `post.id` 作为 key。它帮助插入、删除、排序时保持 item 身份与对应状态，不能保证条目永不重组。`contentType` 用于区分可复用内容类型，当前这处列表没有显式配置。

编译器稳定性、参数是否变化、实际 State 读取和 key 是不同维度。Strong skipping 改变了可跳过条件，当前官方说明从 Kotlin 2.0.20 开始默认启用；本项目声明的插件版本高于这一版本，但实际编译行为仍应看构建配置和编译报告。**不能直接给类加 @Stable/@Immutable 来消除真实可变性。** 官方：[Strong skipping](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping)、[Lazy lists](https://developer.android.com/develop/ui/compose/lists)。

### 4.3 为什么不能在 Composable 主体直接发请求

Composable 可能重复执行，也可能跳过或取消本轮组合。直接在函数体执行刷新或写库，会把“描述 UI”变成“重复业务副作用”。当前初次刷新由 ViewModel init 发起，而 Effect 收集放在 LaunchedEffect 中，是两种不同职责。

几个 API 的应用边界：
- `LaunchedEffect(key)`：进入组合启动协程，key 改变会取消旧任务并重新启动，离开组合会取消。
- `rememberCoroutineScope`：适合点击回调触发、由组合拥有的工作；不是应用全局任务作用域。
- `DisposableEffect`：用于注册监听并在离开时注销等成对管理。
- `rememberUpdatedState`：让长期 effect 使用最新值而不必因该值重启；不是绕开状态设计。

官方：[Compose side effects](https://developer.android.com/develop/ui/compose/side-effects)。

**项目中的具体追问：** FeedScreen 每分钟更新一次 currentTime，effect key 是 Unit。若它仍留在组合内，切到通知/发布分支并不必然停止这个 effect。FeedScreen 的 `LaunchedEffect(Unit)` 捕获 ViewModel，如果将来调用方允许替换 ViewModel，就应重新审视 key。这里不是已复现 bug，而是改造时必须知道的生命周期边界。

## 5 StateFlow 与 SharedFlow 在这里怎样工作

### 5.1 状态与一次性意图不能混为一谈

`_uiState` 是 StateFlow：始终有一个当前值，适合回答“页面现在是什么样”。它根据相等性合并更新，慢收集者可能看不到每一个中间值，因此不适合充当完整操作日志。官方：[StateFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)。

`_effect = MutableSharedFlow<FeedEffect>()` 使用默认配置。新订阅者不会自动收到过去事件；没有订阅者时，默认无 replay 的事件不会因 `emit` 就永久保存。加入 extraBufferCapacity 也不等于解决无订阅者重放。官方：[SharedFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)。

当前 effect 包括显示提示和滚动到某个位置。对于“发布已经成功”这类重要业务事实，应由可恢复状态表示；提示只是该事实的一种 UI 展示。改成 Channel 也不能自动获得跨进程、跨生命周期的 exactly-once。

### 5.2 当前收集方式需要准确描述

FeedScreen 使用 `collectAsState()` 和普通 `LaunchedEffect(Unit)` 收集 Effect；这与“进入 STARTED 才收集”的生命周期策略不同。组合仍存在时，应用进入后台不必然停止这些收集。

若改进，可以在合适依赖下使用 `collectAsStateWithLifecycle`；事件收集可用 `repeatOnLifecycle` 明确开始/停止。**UI 不收集不代表 ViewModel 的生产协程全部停止**，上游是否停止取决于 scope、共享策略和实现。官方：[生命周期感知协程](https://developer.android.com/topic/libraries/architecture/coroutines)。

### 5.3 UI Effect 自己也可能被阻塞

本项目收到 ShowMessage 后另启 snackbarJob，并取消旧 Snackbar；收到 ScrollToIndex 时却在收集回调中直接执行 `animateScrollToItem`。滚动是挂起过程，期间这个 collector 对后续事件的处理要等待。是否需要排队、取消旧滚动或并行处理，要按交互语义决定，不能为了“更快”随意给每个事件 launch。

练习：在 fake effect 流里连续发送“滚动→消息→滚动”，记录各步时间；再模拟页面停止收集后发布完成，观察哪些提示被丢失、业务状态是否仍能恢复。

## 6 协程并发与一次真实点赞

### 6.1 当前点赞链路

```text
FeedPostItem 点击
  → FeedScreen 根据当前 post.isLiked 发送 LikePost 或 UnlikePost
  → FeedViewModel.handelIntent
  → viewModelScope.launch
  → LikePostUseCase
  → FeedRepositoryImpl.likePost
       _feedPosts.update { map + copy + likedUsers追加 }
       persistPostsToDb 在 IO 中重写缓存
  → UseCase 按帖子归属条件生成通知
  → Repository Flow → ViewModel UiState → UI
```

这条链路当前是本地数据更新。虽然 FeedApiService 定义了 like/unlike/comments 方法，Repository 的对应方法并没有调用它们。不能讲成“服务端返回成功后更新点赞”，也不能宣称做了远端幂等键、冲突合并或失败回滚。源码：[domain/usecase/LikePostUseCase.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/domain/usecase/LikePostUseCase.kt)；[data/FeedRepositoryImpl.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/FeedRepositoryImpl.kt)；[data/network/FeedApiService.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/network/FeedApiService.kt)。

### 6.2 三种并发保证要分开

1. StateFlow 自身方法线程安全。
2. `update { old -> new }` 对一个 StateFlow 值做原子更新。
3. “检查帖子→更新内存→写库→加通知”这一整项业务是原子的。

前两项不能推出第三项。`update` 的 lambda 可能重试，所以里面应尽量只计算新值，不发送网络请求、写库或做不可重复的埋点。官方：[MutableStateFlow.update](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/update.html)。

本项目点赞逻辑先找帖子，再把用户追加到 likedUsers。UI 切换按钮能减少重复点击，却不是仓储幂等约束。如果相同 LikePost 被重复投递，应测试是否出现重复用户；通知的去重也不等于帖子点赞列表的去重。

另一个实验是同时刷新与点赞：刷新用远端列表替换整个状态，可能覆盖本地刚发生的操作。解决方案可包括每条帖子的操作串行化、明确版本冲突策略或本地真相源；不要先套一个 Mutex 就宣称解决所有网络一致性问题。

### 6.3 suspend 和 IO 不是同义词

`suspend` 允许挂起，不自动切后台线程。`viewModelScope.launch` 默认围绕主线程运行；Retrofit 的异步网络能力不会自动把之后的 SQLite 查询、Gson 反序列化、图片压缩都搬到后台。

建议让数据层提供 main-safe 的挂起方法，由真正执行阻塞工作的一层负责合适的 dispatcher。CPU 密集计算、阻塞文件/数据库操作和非阻塞网络等待也不是完全相同的负载。官方：[Android 协程最佳实践](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)。

### 6.4 取消与异常

本项目 refresh 的网络部分 `catch (Exception)`，ViewModel 外层还有 `runCatching`。两者都需要检查 CancellationException 的传播：取消不是应被转换成“网络失败然后继续回退”的普通业务错误。协程取消主要是协作式的，阻塞第三方调用是否及时停止还需验证。

安全练习：用可取消的 fake 请求，取消 refresh Job，断言不会继续写缓存或显示“刷新成功”。然后分别测试真实 Retrofit 取消和慢 SQLite 操作；两者不能靠同一个假设概括。

## 7 SQLite 缓存的实现与遗漏

### 7.1 当前数据库怎样存储

LocalDatabaseHelper 创建帖子、通知两张表，主键是 id，另有时间列和 JSON 字符串。Gson 自定义 FeedMediaAdapter 用 type 区分图片与视频。优点是结构简单、嵌套对象容易落盘；代价是局部查询/更新不方便，字段演进和损坏数据处理要手动维护。

批量插入方法内部使用事务，并以 CONFLICT_REPLACE 写入；查询通过 `cursor.use` 关闭游标。这些是代码已经体现的细节。`onUpgrade` 当前为空，因此不能说已经实现安全数据库迁移。源码：[data/database/LocalDatabaseHelper.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/database/LocalDatabaseHelper.kt)。

### 7.2 不是所有读写都已切到 IO

- Repository 构造器 init 直接读库。MainActivity 的 ViewModel 创建路径会构造 Repository，存在主线程访问数据库的风险。
- `refreshFeed()` 里的删表、插入、缓存查询没有显式 withContext(IO)。
- `persistPostsToDb()` 和 `persistNotificationsToDb()` 才明确切到 IO。

因此简历只能准确说“部分持久化写入切换到 IO”，不能笼统声称“全部数据库操作异步化”。是否已经造成明显卡顿，要用实际数据量和追踪验证。源码：[MainActivity.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/MainActivity.kt)；[data/FeedRepositoryImpl.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/FeedRepositoryImpl.kt)。SQLiteOpenHelper 的打开与升级可能耗时，官方也提示不要在主线程进行：[API 文档](https://developer.android.com/reference/android/database/sqlite/SQLiteOpenHelper)。

### 7.3 批量插入有事务不等于整体替换原子

当前调用顺序是 `deleteAllPosts()`，随后 `insertPosts()`；事务在后者内部开启。若两步之间失败，旧数据已经删除。多个持久化任务交错时也应检查覆盖问题。

建议把“删除旧集合+插入新集合”放在同一个事务和明确定义的串行写入边界内。另一个方案是按 ID 更新变化项，但需要考虑删除标记和版本。不要把“使用 SQLite”直接等同于“整个业务天然事务化”。官方背景：[SQLite 存储](https://developer.android.com/training/data-storage/sqlite)。

### 7.4 与 Room 的关系

Room 是 SQLite 上层抽象，提供实体/DAO、SQL 校验等能力，不是另一种独立数据库。迁移 Room 可以改善类型与维护体验，但仍要设计线程、事务、数据模型和迁移测试。当前 Room 仅出现在版本目录别名和 README 描述中，app 未接入相应实现，不应算现有项目成果。

**面试回答建议：** “当前版本实际使用 SQLiteOpenHelper 与 Gson 保存帖子快照。它适合演示规模，但我能指出全量替换的事务边界、主线程读库及迁移缺失；如果继续改进，会先把这些行为验证和修正，再决定是否引入 Room。”其中“我能指出”只有真正理解后才能作为个人回答。

## 8 Retrofit 网络边界与错误模型

Retrofit 将接口声明映射为 HTTP 调用，Gson converter 负责响应数据转换，底层 HTTP 客户端完成连接等工作。接口返回 List、Response<List> 或自定义 Result，对状态码、响应体和异常的处理方式会不同，不能背同一套结果判断。

当前 FeedApiService 返回 nullable List，Repository 把请求异常合并成 null。这样会丢掉“无网络、超时、HTTP 错误、数据格式错误”等区别。RetrofitClient 没有展示自定义认证、缓存、重试、拦截器配置；不要把这些通用能力说成已经实现。源码：[data/network/FeedApiService.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/network/FeedApiService.kt)；[data/network/RetrofitClient.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/data/network/RetrofitClient.kt)。

另外，数据库 JSON 使用注册过 FeedMediaAdapter 的 Gson，但 Retrofit 的 GsonConverterFactory.create() 使用的是默认 Gson 配置。若将来服务端返回多态 FeedMedia，必须验证网络模型的反序列化，不能因为本地缓存能读就认为远端也能解析。可用 DTO 映射或统一、适当配置的 converter 解决，方案需根据真实响应选择。

建议练习四个网络结果：200 空列表、200 格式错误、401/500、断网。UI 应能分清“确实没有帖子”和“请求失败但展示缓存”。对于重复提交，先定义操作幂等性再考虑重试；盲目重试发帖/评论可能重复创建内容。

## 9 媒体选择与发布的真实原生链路

### 9.1 选择图片和视频

FeedScreen 与 PublishScreen 使用 `rememberLauncherForActivityResult` 和 `PickMultipleVisualMedia(9)`。返回 URI 后，通过 ContentResolver 的 MIME 类型区分图片与视频，然后更新媒体列表。

这是使用系统选择器获取所选内容访问权，不是申请读取整个相册。不要把所有 Android 版本都统一说成必须申请 READ_EXTERNAL_STORAGE。官方：[Photo picker](https://developer.android.com/training/data-storage/shared/photo-picker)。

Activity Result 的 launcher 注册与结果处理应和宿主重建相容。调用外部页面期间自己进程可能被回收，输入草稿、临时输出位置与返回结果的关联需要单独考虑。官方：[Activity Result](https://developer.android.com/training/basics/intents/result)。

### 9.2 当前拍照和录像不是自研相机

- 拍照使用 TakePicturePreview，拿到的是预览 Bitmap，不应宣传为完整分辨率拍照流程。
- 回调把 Bitmap 压缩成 JPEG 并写入 cacheDir；当前回调里这段工作没有显式切 IO，值得测量主线程耗时。
- 录像使用 ACTION_VIDEO_CAPTURE 和 StartActivityForResult，委托外部相机，再读取返回的 URI。
- Manifest 当前声明 INTERNET；没有自建 CameraX/Camera2 管线。

这不代表功能一定有问题，而是实现边界不同。自建相机、调用系统相机和系统 Photo Picker 的权限要求不同；平台版本、intent 和是否自行声明 CAMERA 都应一起核对，不能机械补全一长串权限。源码：[presentation/FeedScreen.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/FeedScreen.kt)；[presentation/components/PublishScreen.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/components/PublishScreen.kt)；[app/src/main/AndroidManifest.xml](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/AndroidManifest.xml)。

### 9.3 发布媒体现在保存在哪里

发布按钮先在 `rememberCoroutineScope` 中启动任务；将 content URI 通过 ContentResolver 复制到本地，复制部分切到 IO；随后调用 onPostClick。父页面发送 CreatePost Intent 并切回 Feed 页面，ViewModel 再做本地创建与持久化。

```text
系统返回 content URI
  → 发布页选中媒体
  → 点击发布
  → IO 中读取 URI，复制到 cacheDir
  → onPostClick 回调
  → FeedViewModel 发起本地 CreatePost
  → Repository 更新内存并持久化
  → Effect 提示和滚动
```

`copyUriToLocalCache` 用的是 **cacheDir，不是 filesDir**。缓存文件可能被清理，即使数据库还保存路径，媒体也不保证永久存在。函数遇异常返回原 URI；若 openInputStream 返回 null，当前代码仍可能返回未真正写成的本地文件 URI。这些是应补测的输入边界，不能用“已复制”代替成功验证。源码：[presentation/components/PublishScreen.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/components/PublishScreen.kt)。

URI 字符串不是永久访问权，也不是普通绝对文件路径。是否能持久化权限取决于来源及授权；长期使用可按来源申请可持久化授权，或把内容复制到应用管理的合适存储并管理清理策略。官方：[共享文件与 URI 权限](https://developer.android.com/training/data-storage/shared/documents-files)。

### 9.4 发布中的状态不能只靠弹窗

当前 isPublishing 是发布页的本地状态，onPostClick 本身不是等待仓储完成的挂起回调。页面发出 Intent 后就切换，并不意味着落库结果已确认。点击禁用条件也应包含发布中状态，而不只是文字/媒体非空。

练习：复制失败、磁盘写入失败、点击后旋转、连续点击、复制结束前离开页面。设计时明确哪些失败应保留草稿、哪些步骤可取消、什么时候才宣布成功。`finally` 可以帮助清理 loading，但并不替代完整结果模型。

## 10 Coil 列表和视频资源

### 10.1 以真实测量解释列表优化

本项目使用 AsyncImage、LazyColumn stable key、不可变列表更新。这些是实现手段，不直接证明帧率提升多少。图片解码尺寸、网络请求、布局复杂度、重组范围、排序与 JSON 工作都可能影响滑动。

建议固定同一设备、构建模式、数据和图片缓存条件，再测量滚动帧耗时与卡顿。不要用 Debug 包的一次肉眼观察声称稳定60 FPS；高刷设备每帧预算也不同。官方：[Macrobenchmark](https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview)。

Coil 的 AsyncImage 能结合布局约束进行适当加载；原尺寸图片、巨大 Bitmap 或反复变化的请求键仍可增加负担。当前代码中的演示头像 URL 使用时间戳，学习缓存命中时应知道这会改变请求身份。官方：[Coil Compose](https://coil-kt.github.io/coil/compose/)。

### 10.2 视频封面与播放不是同一个资源

VideoThumbnailHelper 在 IO 中创建 MediaMetadataRetriever，获取帧，并在 finally 中 release。`LaunchedEffect(videoUrl)` 加载封面，remember(videoUrl) 保存 Bitmap。它展示了资源成对释放，但不能据此说拥有完整视频封面缓存、内存上限或取消可中断全部 native 解码的保证。源码：[presentation/components/VideoThumbnailHelper.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/components/VideoThumbnailHelper.kt)。

VideoPlayerDialog 则通过 AndroidView 创建 VideoView，配置 MediaController，并在准备完成时循环播放。当前组件未显式实现覆盖全部前后台/关闭场景的暂停、播放位置恢复及释放回调。不要直接断言泄漏已经发生，也不要断言框架必然替你处理所有媒体生命周期。应测试实际行为，再按所有权设计停止/恢复/释放。源码：[presentation/components/FeedPostItem.kt](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/src/main/java/com/hejulian/testdemo/presentation/components/FeedPostItem.kt)；官方：[媒体状态和资源](https://developer.android.com/media/platform/mediaplayer/state-resources)。

## 11 原生底层原理怎样联系到这个项目

### 11.1 Handler Looper 和主线程

Looper 在所属线程处理消息，Handler 把消息/任务投递到指定 Looper 的队列。回到主线程不是创建了一条新线程，而是把工作安排给主线程执行。协程和 Compose 没有让主线程可以无限承载阻塞任务。官方：[Handler](https://developer.android.com/reference/android/os/Handler)、[Looper](https://developer.android.com/reference/android/os/Looper)。

在 FeedLine 中，数据库 init、refresh 的同步数据库段、拍照回调压缩写文件，都可以作为检查主线程负载的具体入口。排查时记录线程名、耗时和 trace；不能看到 suspend 就跳过这些位置。

### 11.2 ANR 掉帧 OOM 不同

- 掉帧：未及时完成显示帧，可能短时卡顿但尚未触发 ANR。
- ANR：某类系统交互未在规定时间内得到响应；不同类型阈值与条件不同，不能一律背“主线程五秒”。
- OOM：内存分配失败，图片/视频 Bitmap、重复解码等应纳入排查。

主线程等待后台持有的锁、同步 Binder 调用或慢磁盘，也可能造成响应问题；不只是死循环。FeedLine 的第一步应是结合 trace、主线程栈和复现步骤定位，而不是先把所有方法改成 IO。官方：[ANR](https://developer.android.com/topic/performance/issues/anr)。

### 11.3 GC 为什么不等于资源都释放

GC 处理不再可达的托管对象；仍被静态字段、监听器、队列或长任务引用的 Activity 不会因此消失。文件描述符、数据库游标、播放器和 native 解码资源也要遵守各自的释放协议。

练习：反复打开/关闭发布页、全屏视频与大图，观察资源实例数、堆内存和返回后的行为，区分短期缓存与持续增长。项目中 `cursor.use` 与 retriever.finally.release 是可讲的良好局部实践，不应扩大成“项目不存在内存泄漏”。

## 12 构建与可测试性

### 12.1 能讲清怎样从零运行

从 README、Gradle wrapper、AGP、JDK、SDK 和版本目录开始，区分 compileSdk、targetSdk、minSdk。源码声明 Java source/target 11 不等于 Gradle 守护进程运行 JDK 就必须是11；AGP 运行要求应按对应版本核对。

项目混用了 Compose BOM 和显式版本。用 dependencies / dependencyInsight 检查最终选择，而不是看到两个声明就断言冲突已经发生。`release` 配置中的优化关闭也提醒我们：不能未经配置和基准核对就说已完成 R8 或 Baseline Profile 优化。源码：[app/build.gradle.kts](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/app/build.gradle.kts)；[gradle/libs.versions.toml](https://github.com/hejulian2004/testDemo/blob/8aa963a945176f8d5903b0b706423fd95cc011ff/gradle/libs.versions.toml)。

### 12.2 当前测试证明了什么

可见默认测试是简单算术与包名检查，没有形成覆盖刷新、缓存、取消、媒体恢复等业务的测试证据。本次也没有运行这些测试。面试时不要把“项目有 test 目录”说成“核心逻辑已完整自动化验证”。

建议分层补测：
- JVM 单元测试：ViewModel/UseCase 用 fake Repository；明确虚拟时间与调度器。
- 数据层测试：缓存损坏、事务失败、升级旧库、并发持久化。
- Compose UI 测试：按语义查找控件，验证状态与交互，不依赖脆弱坐标。
- 设备测试：媒体 URI、旋转、后台恢复、播放器与文件存储行为。

Repository 当前直接依赖全局 Application Context，ViewModel 默认埋点实现会调用 Android Log/Toast。把数据源、dispatcher、tracker 作为可替换依赖，有助于隔离测试；这是建议，不代表现有设计已经完全可测试。

## 13 二十个需要结合代码回答的追问

下列回答是准备方向，不是可以直接背诵的个人经历。

### A01 为什么项目 README 写 Room 但你说 SQLiteOpenHelper

以固定提交的执行代码和 app dependencies 为准。README 与版本别名不是运行证据；说明实际数据表、JSON adapter 和事务实现，再指出文档待同步。

### A02 为什么页面看起来刷新成功但服务器可能从未连通

配置是占位服务地址；Repository 捕获异常后缓存或假数据回退，ViewModel 以函数未抛异常判断成功。需要把网络状态和展示状态分开。

### A03 ViewModel 能解决发布草稿丢失吗

仅在草稿实际由它持有且 owner 存活时有帮助。当前文字在 PublishScreen 的 remember 中；进程死亡还需要保存/持久化策略。

### A04 collectAsState 与 collectAsStateWithLifecycle 在项目中有何区别

当前采用前者，收集跟组合关联；后者可按 Android lifecycle 活跃状态收集。停止 UI 订阅不自动取消所有 ViewModel 工作。

### A05 为什么 SharedFlow 发出了事件仍可能没提示

默认无 replay，没有订阅者时事件不保留。生命周期切换、订阅建立时序以及 collector 内挂起都要考虑。关键成功状态不应只存在于一次性提示中。

### A06 stable key 为什么不能保证只有点赞项重组

key 处理 item 身份；重组还取决于参数、可观察状态读取、编译器跳过策略等。应测量后判断范围，不从 key 推导帧率。

### A07 为什么原地改 likedUsers 容易出问题

普通集合内部变化不一定触发可观察状态更新，旧引用也可能被共享。当前 copy + 新列表更清晰，但业务幂等与持久化并发仍要另外保证。

### A08 update 已经原子了为什么还可能重复点赞

原子的是某次值更新，不是完整业务流程；若重复 Intent 每次都追加用户，原子执行也会忠实产生重复数据。需要业务约束与测试。

### A09 为什么刷新可能覆盖刚发布或点赞的内容

刷新以新列表整体替换状态，本地改动没有独立同步状态/版本冲突规则。先定义缓存和远端谁是真相源，再选择合并策略。

### A10 suspend 的 refresh 为什么仍可能卡 UI

挂起签名不迁移普通代码。网络之后的同步数据库操作可回到调用线程；init 更是普通构造路径。定位实际线程才有结论。

### A11 为什么 catch Exception 需要关心取消

CancellationException 也是异常；吞掉后可能继续回退/写库/发成功提示，违背取消意图。应区分取消与业务失败，并验证底层是否响应取消。

### A12 批量 insert 有事务为什么还会丢旧数据

delete 在该事务外。替换整体的原子边界必须覆盖删除和插入，不能只看 helper 某个方法有 beginTransaction。

### A13 能直接把数据库版本3改成4吗

先定义升级路径和兼容策略。当前 onUpgrade 为空，没有证据表明旧版本能安全迁移；应创建旧库样本并执行升级测试。

### A14 为什么缓存 JSON 能解析不能证明网络 JSON 能解析

两处 Gson 配置不同。数据库注册了 FeedMediaAdapter，Retrofit 默认 converter 未注册相同多态配置，需要真实响应测试。

### A15 为什么选图不需要申请整个相册权限

系统选择器可以授予所选 URI 的访问权；这是最小访问范围。自建相册扫描与系统 Picker 不是同一种权限模型。

### A16 copyUriToLocalCache 返回了路径就代表保存成功吗

不是。输入流可能为 null，异常分支会回退原 URI，而且 cacheDir 可被清理。应验证流读取、文件存在/大小、失败结果和存储寿命。

### A17 拍照预览 Bitmap 与完整照片有什么区别

TakePicturePreview 返回预览图。若要求原图，需设计输出 URI、文件提供、结果验证与清理，并按采用的契约处理权限。

### A18 全屏视频关闭就一定释放播放器吗

不能只凭 UI 不显示判断资源释放。应检查 AndroidView/View 的实际生命周期、暂停停止回调与释放行为，并在设备上反复验证。

### A19 有埋点接口就能说提高了转化率吗

当前只看到 Log/Toast。没有生产采集、口径、样本和对照，就不能声称转化率提升；可讲解耦设计及如何验证事件触发。

### A20 如果只给你一天改进最先做什么

先选可验证的一项：例如主线程数据库访问和刷新结果语义，或全量替换事务。写出失败测试，再做小改动；不要先增加更多架构层掩盖现有行为。

## 14 七个能形成面试证据的练习

这些是建议新做的实验，不是历史成果。记录实际版本、设备、输入、观察结果和修改。

| 练习 | 输入或操作 | 验收重点 |
| --- | --- | --- |
| 刷新状态 | 缓存先发、网络延迟，连续刷新两次 | loading 来源清楚；旧请求不覆盖新结果；提示能区分缓存回退 |
| 协程取消 | 等待网络时退出 scope | 无取消后“成功”提示或未经设计的继续写入 |
| 数据库事务 | 在删除后/插入中注入失败 | 原缓存不会留下半套数据；事务范围与恢复策略可解释 |
| 点赞并发 | 同一 post 同一 user 重复 Intent，并叠加刷新 | 无重复点赞；最终状态与业务规则一致，内存与磁盘一致 |
| 草稿恢复 | 输入内容后旋转、后台进程回收再恢复 | 小状态恢复与持久化界限清楚；不会误显示永远发布中 |
| URI 与复制 | null 流、异常流、大视频、复制中取消、清理缓存 | 不伪报成功；不生成悬空媒体记录；资源关闭且主线程不阻塞 |
| Compose 与视频 | 快速滑动、反复开关全屏、切后台 | 用记录解释重组与卡顿；视频行为符合前后台规则，资源不持续增长 |

**建议保留的实验记录模板：**

```text
核对版本：
待验证假设：
复现输入：
预期业务行为：
实际日志或测试断言：
根因对应的代码位置：
最小修改：
回归范围：
仍未验证的条件：
AI 参与部分与我亲自完成部分：
```

进程回收测试与“不要保留活动”不是同一个测试；只做 Activity 重建不能证明进程死亡恢复。构造失败应优先使用 fake 数据源、可控文件流和测试数据库，不要在用户真实数据上试破坏。

## 15 面试主线如何收束

对 Android 实习而言，FeedLine 最适合证明的是：能把原生生命周期、声明式 UI 状态、协程、存储与系统媒体能力连起来，并能定位边界错误。无需把演示项目包装成生产级社交系统。

可以按真实掌握程度组织项目介绍：

> FeedLine 是 Kotlin 与 Compose 实现的信息流练习，采用 ViewModel、Intent/State/Effect 和 Repository 分层。当前版本本地状态与 SQLiteOpenHelper/Gson 缓存是主要实现，网络接口存在占位配置。我能展开的是【本人真正理解的链路】，并通过【自己执行的测试】验证了【具体行为】。对于生命周期感知收集、数据库整体替换事务或媒体持久化等问题，我会按当前代码说明限制，不把计划改进说成已经完成。

把括号填成真实事实。建议先讲“刷新如何到达页面”，再接受“取消、旋转、断网、写库失败时会怎样”的追问。能够回答这些，比列出更多未使用的 Jetpack 组件更有说服力。
