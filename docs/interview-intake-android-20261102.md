# Android 面经补充：缓存、网络封装与设备场景

整理与技术核对：2026-11-02。本篇根据用户提供的文字面经及截图中的**题意线索**独立编写参考答案，补充现有题库未展开的工程角度。原帖 URL 和实际面试日期未核取，公司、轮次及经历仅为分享者自述；不进入原有三年已核来源统计，也不表示这些方案已在你的项目中实现。

优先学习 AD01—AD10 的缓存、网络和构建链，再练 AD11—AD15 的媒体与设备场景。题号与路径独立于其他指南，同名编号不代表同一道题，网站以“路径＋编号”保存进度。本文示例为设计与排障练习，未编译 Android 示例，未进行设备、代理、传感器或音频测试。Android/AndroidX/OkHttp 行为须对照实际依赖及 targetSdk；所链官方主分支源码会变化。

基础概念已有入口：自定义 View 和事件分发见 [XML 指南 Q07—Q10](word-crush-android-xml-guide.md#q07)；ViewModel 与进程恢复见 [平台指南 AD01—AD02](android-platform-interview-guide.md#ad01)；Flow/取消见 [协程指南 KT22—KT40](kotlin-coroutines-interview-guide.md#kt22)。下列问答不把候选人的音乐、机器人或实习项目改写成你的项目事实。

## 缓存与界面

<a id="ad01"></a>
### AD01 P0 歌曲离线下载、边播边缓存和直接 URL 播放应怎样分开设计

**口述回答：** 先分清保存的是歌曲元数据还是音频字节。数据库保存歌曲 ID、版本、下载状态等；完整离线内容和可淘汰的播放缓存分别管理。Media3 可以用 `CacheDataSource.Factory` 串接缓存与网络数据源，命中已有字节范围时本地读取，未命中再访问上游；主动离线下载另有 DownloadManager/DownloadIndex。只把远端 URL 交给播放器，不等于已经有持久缓存。

**原理与边界：** 缓存键应对应同一份真实内容和权限范围，例如业务媒体 ID＋清晰度/编码＋内容版本，并按需要隔离账号。临时签名 URL 变化不一定意味着音频变化，但不能不经业务判断就删除所有查询参数；不同音轨或用户内容可能因此串数据。播放缓存设总字节上限和淘汰策略，离线下载则有完整性、失败恢复及用户删除语义。临时缓存目录可能被系统清理；HTTP 缓存、元数据缓存与媒体分段缓存不是同一个东西。

**追问：URL 过期但已缓存部分内容，还能播放吗？答：** 已命中字节可能可读，后续缺失范围仍需可用的 URL 和鉴权。应在数据源或资源解析层更新地址，保持内容身份一致；不能把“播过一次”当成完整离线。

**易错点：** 为了离线播放先将整首歌读入内存；把 Glide 图片缓存或 OkHttp HTTP 缓存直接当成完整媒体下载管理；对用户明确下载的文件随意采用播放缓存 LRU 淘汰。

**官方参考：** [Media3 网络与播放缓存](https://developer.android.com/media/media3/exoplayer/network-stacks#caching-media)；[离线下载与持久状态](https://developer.android.com/media/media3/exoplayer/downloading-media)。

<a id="ad02"></a>
### AD02 P0 用 Hilt 注入音频缓存时，怎样选择作用域与释放责任

**口述回答：** 将缓存、数据源工厂和播放器分别看待。同一缓存目录的 SimpleCache 应由一个明确所有者创建和复用，可在进程内放入 Hilt 的 SingletonComponent，以应用 Context 创建；Repository 或播放器工厂通过构造注入使用它。页面播放器按页面或播放服务的业务生命周期释放，不能因为共享缓存就把 Activity、View 或所有播放器都做成单例。

**原理与边界：** `@InstallIn` 决定绑定可用的组件，`@Singleton` 等 scope 决定同一个组件实例内的复用；只写 `@Provides` 不等于一定单例。`@ApplicationContext` 避免缓存无意保留 Activity，但不替代线程安全。Hilt 作用域也不自动调用任意对象的 `release()`；应在选定的所有者退出时显式释放。多进程各自拥有依赖图，不能依赖进程内单例协调多个进程同时访问同一目录。

**追问：缓存和播放器都放 ViewModelScoped 可以吗？答：** 要先看是否需要跨多个 ViewModel 共享。若每个 ViewModel 各建一个指向相同目录的 SimpleCache，会违反该目录同一时刻单实例的要求。页面资源可以较短，底层共享缓存可以较长。

**易错点：** “单例天然线程安全”；“Hilt 自动释放所有 Closeable”；“Application.onTerminate 能作为真机进程可靠退出通知”。

**官方参考：** [Hilt 组件、作用域和 Context qualifier](https://developer.android.com/training/dependency-injection/hilt-android#component-scopes)；[SimpleCache 单目录实例约束](https://developer.android.com/reference/androidx/media3/datasource/cache/SimpleCache)。

<a id="ad03"></a>
### AD03 P0 ViewPager 嵌套 RecyclerView 时，如何判断并解决滑动冲突

**口述回答：** 先确认是旧 ViewPager 还是 ViewPager2，内外滚动方向相同还是正交，再确定边界时希望谁接管。横向翻页嵌套纵向列表，通常按移动方向和 touchSlop 判断手势；同方向嵌套更需要根据子控件 `canScrollHorizontally/Vertically` 判断它是否还能消费当前方向。在子控件应处理的阶段请求父级不拦截，到边界按约定允许父级接管。

**原理与边界：** `requestDisallowInterceptTouchEvent` 是拦截协商，不是把事件复制给两个控件；父容器中途拦截时，原子目标会收到 ACTION_CANCEL，应清理拖动、速度与按压状态。ViewPager2 官方迁移指南提供同方向嵌套的 wrapper 示例，但不能直接推出所有多层嵌套都被解决。NestedScrolling 的滚动距离协商与原始触摸事件拦截也不是同一层机制。

**追问：一直禁止父容器拦截最省事，为什么不行？答：** 可能使翻页失效，或到子列表边缘仍无法切页；还可能影响多指、斜滑和可访问性操作。需要用中间区域/两端、慢拖/快甩、横竖斜、多指和 CANCEL 做验证。

**易错点：** 在所有 ACTION_MOVE 返回 true；忽略 DOWN 的目标确定和 CANCEL；把关闭 nestedScrolling 当成通用答案。

**官方参考：** [ViewPager2 同方向嵌套滚动](https://developer.android.com/develop/ui/views/animations/vp2-migration#nested-scrollables)；[ViewGroup 拦截、CANCEL 与 touchSlop](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)。

<a id="ad04"></a>
### AD04 P1 瀑布流怎样按当前窗口宽度自适应列数，必须自定义 LayoutManager 吗

**口述回答：** 不一定。不同高度卡片可以使用现有 StaggeredGridLayoutManager，根据 RecyclerView 实际可用宽度算 spanCount，仅在列数变化时更新。可用宽度要减去控件 padding，并把间距、最小卡片宽度换成相同单位；不能按设备型号或整块物理屏幕宽度写死，因为分屏、窗口缩放和折叠都会改变实际空间。

**原理与边界：** 若可用宽度为 W、最小卡片宽度为 m、列间距为 g，一个简化约束是 `n = max(1, floor((W + g) / (m + g)))`，前提是 W 已扣除外侧装饰，m/g 为正且未重复扣间距。“小屏两列”还要确认两列满足可读宽度；业务强制两列时应明确下限策略。设置 spanCount 会使原 span 分配失效并触发布局，避免布局计算期间反复修改；图片应尽量提前有比例，减少高度跳变。等高规则网格可选 GridLayoutManager，无需为了自适应重复实现布局算法。

**追问：每次 onBind 都重新计算列数可以吗？答：** 不应让单个 item 的绑定控制整个布局。根据容器尺寸变化统一更新，并验证滚动位置、全宽标题项和快速旋转时的一致性。

**易错点：** 像素与 dp 混算；认为 StaggeredGridLayoutManager 自动根据宽度推导列数；为了两列到三列变化重写整套测量和回收逻辑。

**官方参考：** [StaggeredGridLayoutManager.setSpanCount 的失效与布局行为](https://developer.android.com/reference/androidx/recyclerview/widget/StaggeredGridLayoutManager#setSpanCount(int))；[窗口大小分类与自适应设计](https://developer.android.com/develop/ui/compose/layouts/adaptive/use-window-size-classes)。

## 网络封装与构建

<a id="ad05"></a>
### AD05 P0 基于 OkHttp 封装网络库，怎样避免所有逻辑都塞进拦截器

**口述回答：** 网络基础设施层负责客户端复用、连接、超时、代理、Cookie、日志和 HTTP 缓存；API/数据源层描述端点与序列化；Repository 结合远端与本地并产生领域结果；ViewModel 将结果转成 UiState。Retrofit 可以承担接口和转换适配。先按变化原因分职责，再决定抽象，不能只把一个 request 方法包装几次就声称形成完整架构。

**原理与边界：** 共享 OkHttpClient 通常有利于复用连接池和线程池，不等于所有账号共享同一登录状态。拦截器适合与 HTTP 请求/响应相关的横切逻辑；账号切换、页面导航和业务库存等不应直接由底层发起。日志必须控制敏感头和请求体，缓存键/鉴权隔离也要有业务约束。新增上传方法可以对外使用窄接口与可替换的数据源，但不强行为每个简单调用建立庞大框架。

**追问：怎样测试这层封装？答：** 在 API/Repository 的替身之外，还测试真实 HTTP 行为：重定向、超时、重复 Cookie、错误响应体、取消及大文件。UI 测试不能单独证明网络层的资源释放和幂等。

**易错点：** 每次请求都新建客户端；所有错误都自动重试；底层库持有页面或直接弹 Toast。

**官方参考：** [OkHttpClient 的复用契约（官方源码）](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/OkHttpClient.kt)；[Android 数据层的 Repository 与数据源](https://developer.android.com/topic/architecture/data-layer)。

<a id="ad06"></a>
### AD06 P0 成功、业务失败和异常怎样统一处理，公共错误都放拦截器吗

**口述回答：** 分开传输失败、HTTP 状态失败、业务错误码和解析失败，再在约定边界转为领域结果；UI 层才映射加载、内容和可重试提示。密封结果类型可让 when 分支在适用条件下接受穷尽检查，避免调用者把失败当成空列表。公共映射可以复用转换器或执行模板，不必在每个 Repository 粘贴一组 catch，也不必把所有业务规则下沉到 OkHttp。

**原理与边界：** 拦截器能统一请求头、HTTP 级度量或约定的认证处理；任意业务 JSON 的错误码还受内容类型、API 版本和流式响应约束。提前消费 ResponseBody 后必须明确如何交付下游，不能读两次就假设数据仍在。应用拦截器与网络拦截器在缓存、重定向和重试下的调用次数不同。协程 CancellationException 应继续传播，而不是包装成普通失败或触发重试。

**追问：HTTP 200 是否一定 Success？答：** 只说明 HTTP 层这次响应状态；业务包可能报告拒绝、限流或权限过期。反过来，网络超时也不能证明服务端没有执行写操作，重试需要业务幂等或状态查询。

**易错点：** 把所有 Throwable 吞成 Result.Failure；认为密封类自动防止错误归类；在全局拦截器里解析所有响应并直接切登录页面。

**官方参考：** [OkHttp Call 对传输成功与业务成功的区分](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Call.kt)；[应用/网络拦截器差异](https://github.com/square/okhttp/blob/master/docs/features/interceptors.md)；[及时取消的 API 规则](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/suspend-cancellable-coroutine.html)。

<a id="ad07"></a>
### AD07 P0 收到 Set-Cookie 如何保存和再次发送，需要加锁吗

**口述回答：** 优先用 OkHttp CookieJar 的 `saveFromResponse` 与 `loadForRequest` 承接 Cookie 策略和存储；按域、路径、安全属性、过期时间等选择适用于目标 URL 的 Cookie。多个异步请求可能并发读写同一个 jar，因此共享可变存储需要同步设计，而不是仅在某次写文件前随手加一把锁。

**原理与边界：** Cookie 的覆盖身份通常涉及 name、domain、path；不能只用 name，也不能用逗号把整个 Set-Cookie 拆开。加载应返回一致快照；“清理过期＋替换同身份项＋读取”若是复合操作，需要同一事务/锁或单一所有者协调。ConcurrentHashMap 只保证其规定的单次操作，不自动保证这些步骤整体原子。logout 和迟到响应还可能竞争，应按账号/会话版本防止旧响应重新写入登录状态；持久化与进程内同步也要分别设计。

**追问：只用拦截器拼 Cookie 请求头可行吗？答：** 能实现特定规则，但你就承担了匹配、过期、重定向及并发的正确性。已接入 CookieJar 时不要再重复拼一套，以免重复或泄露到错误域。

**易错点：** 所有域发同一组 Cookie；只同步写入却允许无同步遍历；认为 HttpOnly 代表 native CookieJar 会自动提供安全持久化。

**官方参考：** [OkHttp CookieJar 官方契约](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/CookieJar.kt)；[RFC 6265 存储模型与匹配](https://www.rfc-editor.org/rfc/rfc6265#section-5.3)。

<a id="ad08"></a>
### AD08 P1 OkHttp 需要经过代理时，应配置什么，HTTPS 还安全吗

**口述回答：** 先确认 HTTP 代理、SOCKS 还是按地址选择代理，再配置 OkHttpClient 的 proxy 或 proxySelector。代理认证和源站认证分开，分别处理代理挑战与源站挑战。显式 proxy 优先于 proxySelector；改变路由不是往普通请求里随便添加一个“代理地址”头。

**原理与边界：** HTTPS 经 HTTP 代理通常先建立 CONNECT 隧道，再与目标站做 TLS；代理能否读取内容取决于终端实际信任链和是否进行 TLS 中间人解密，不能一概而论。不能为“能抓包”禁用证书或主机名校验。代理选择、DNS、连接复用和失败回退受客户端与代理类型影响，应通过测试确认。认证重试须有退出条件，避免凭据错误时无限循环，并防止把 Proxy-Authorization 错发到源站。

**追问：怎样明确禁用系统代理？答：** 在需要且合理的场景配置 `Proxy.NO_PROXY`；设置 null 是让显式代理缺省，不等于强制直连。还要核对平台网络策略与实际请求日志。

**易错点：** 混用 authenticator 与 proxyAuthenticator；承诺所有代理都在同一端解析 DNS；把信任任意证书作为正常网络库设计。

**官方参考：** [OkHttpClient proxy、proxySelector 与 proxyAuthenticator（官方源码）](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/OkHttpClient.kt)；[HTTP CONNECT 语义](https://www.rfc-editor.org/rfc/rfc9110#section-9.3.6)。

<a id="ad09"></a>
### AD09 P0 OkHttp 如何结合协程，取消和响应体所有权怎样对齐

**口述回答：** execute 会阻塞执行它的线程；enqueue 调度异步请求，协程可以在等待回调时挂起，OkHttp 内部仍有线程执行网络工作。已有 Retrofit suspend 接口时优先使用其适配，不重复包一层。自封装单次回调时，用 suspendCancellableCoroutine 建立终态，并把协程取消连接到 Call.cancel；收到响应后还要处理取消竞争与 Response 的关闭。

**原理与边界：** 包装流程是：先登记取消钩子，再 enqueue；失败恢复异常；成功时按清晰协议交接 Response；交接前取消或结果恢复后尚未被调用方接收时，必须有关闭资源的路径。单靠 `isActive` 不能消除“检查后立刻取消”的竞争。回调可能迟到，不允许重复恢复。具体 `resume` 的取消清理参数以 kotlinx.coroutines 版本为准。响应体读取与大 JSON 解析还可能耗时，应按消费方式做 main-safe 设计。

**追问：把 execute 放 withContext(IO) 就支持取消了吗？答：** 只解决执行线程选择，不自动让底层阻塞调用响应协程取消。需要底层支持及取消桥接；runInterruptible 也只对正确响应线程中断的 API 有帮助。超时后服务端仍可能完成操作。

**易错点：** “协程不占任何线程”；“suspend 自动转后台”；catch IOException 时直接漏掉 ResponseBody 关闭；把 mounted/页面仍存在式检查当成真实取消。

**官方参考：** [suspendCancellableCoroutine：及时取消与资源交接](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/suspend-cancellable-coroutine.html)；[OkHttp Call 的 execute、enqueue、cancel 契约](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Call.kt)。一般回调适配继续读 [KT28](kotlin-coroutines-interview-guide.md#kt28)。

<a id="ad10"></a>
### AD10 P0 从源码到 APK 的构建链有哪些环节，AAB 又是什么

**口述回答：** Gradle/AGP 根据 variant 组织任务：解析依赖、合并 Manifest 与资源，Java/Kotlin 编译得到 JVM 字节码；AAPT2 编译和链接 Android 资源；D8 将字节码转 DEX，启用的 release 优化链可由 R8 做代码缩减、优化和混淆；最后把 DEX、资源、assets、native 库等组装、对齐和签名。实际任务图有并行和版本变化，不要把口述顺序当成所有 AGP 版本固定流水线。

**原理与边界：** `./gradlew :app:assembleDebug` 是常见可安装调试包入口，模块名和 variant 以项目为准；发布包需要正确签名与构建配置。手动工具链通常先 zipalign 后 apksigner，签名后再改内容会破坏签名。AAB 是发布格式，可由分发工具按设备生成 APK，不是直接安装的 APK。DEX 构建与设备 ART 运行期的解释/JIT/AOT 是不同阶段。

**追问：debug 能运行，release 崩溃，先查什么？答：** 比较依赖/资源、BuildConfig、签名及 R8 配置，检查反射/JNI/序列化的保留规则，并结合混淆映射还原栈。不能用关闭全部优化掩盖缺失规则后就宣布问题解决。

**易错点：** “Android Studio 自己编译全部内容”；“AAPT2 输出了最终可安装应用”；把签名私钥提交仓库；把构建耗时改善说成运行时冷启动改善。

**官方参考：** [命令行构建](https://developer.android.com/build/building-cmdline)；[AAPT2 两阶段资源处理](https://developer.android.com/tools/aapt2)；[D8 输入与 DEX 输出](https://developer.android.com/tools/d8)；[R8 优化](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization)；[apksigner 的对齐与签名顺序](https://developer.android.com/tools/apksigner)。

## 媒体与设备场景

<a id="ad11"></a>
### AD11 P0 Glide 说四层缓存时，分别缓存什么，为什么相同 URL 也可能重新加载

**口述回答：** Glide 4 文档的四次查找是 active resources、memory cache、resource disk cache、data disk cache。前两层是仍在使用或可复用的内存资源；后两层分别保存处理后的资源与原始数据。全部未命中才回到原数据源。它们不能简单合并成“四个 LRU”，也不能只背“内存、磁盘、网络三层”。

**原理与边界：** 模型和 signature 参与缓存键，部分层还包含目标尺寸、变换、选项和资源类型。相同 URL 以不同尺寸或变换展示不保证命中同一处理后资源；DiskCacheStrategy 影响哪些内容读写磁盘。头像更新可用真实版本签名驱动失效，而不是每次绑定追加时间戳。是否缓存原图与处理结果，要结合来源、重用模式和容量验证。

**追问：skipMemoryCache(true) 是否会关闭所有缓存？答：** 不会；它与磁盘缓存策略是不同设置。命中磁盘也通常需要异步读取/解码，不能按内存命中的成本估算列表帧时间。

**易错点：** 把网络称为 Glide 的第四层缓存；忽略 active resources；认为缓存键永远只是 URL；未经测量承诺命中率或性能收益。

**官方参考：** [Glide 4 缓存顺序、键与策略](https://bumptech.github.io/glide/doc/caching.html)。对照项目的使用边界见 [XML 指南 Q16](word-crush-android-xml-guide.md#q16)，不表示项目手写了这套缓存。

<a id="ad12"></a>
### AD12 P1 音乐播放遇到来电、提醒或铃声，怎样处理音频焦点

**口述回答：** 播放前按用途申请焦点，使用匹配的 AudioAttributes；请求失败时不能假装正常播放。收到永久丢失、暂时丢失和可 duck 的变化，要按媒体类型暂停、停止或降低音量；焦点恢复时只恢复被暂时打断且用户仍希望播放的内容。用户在打断期间主动暂停，就不能在来电结束后擅自自动播放。

**原理与边界：** 音频焦点与系统音量不是同一个概念。Android 8 起有 AudioFocusRequest 和特定条件下的自动 ducking，Android 12 起系统对部分焦点切换和来电执行淡出/静音；不能把某台手机上的现象套给所有版本。在运行 Android 15（API 35）或更高版本、且应用 targetSdk 35+ 时，请求焦点还要求应用位于顶部或正在运行前台服务。日历提醒可能仅发无声通知，也可能请求临时焦点，因此需先问清其实际音频行为。自行识别通话状态并不是所有媒体应用必须采用的通用方案。

**追问：后台播放是否只要前台 Service 就不会中断？答：** 前台服务只是一种受限制的运行组件；它不替代焦点管理、播放器状态机和系统资源回收处理，更不保证永久存活。

**易错点：** 来电结束必定自动播放；所有焦点丢失都只设音量为零；假设每次系统 ducking 都会以相同方式回调。

**官方参考：** [音频焦点及版本行为](https://developer.android.com/media/optimize/audio-focus)；[前台服务适用范围与限制](https://developer.android.com/develop/background-work/services/fgs)。

<a id="ad13"></a>
### AD13 P1 插上充电器的一瞬间，是否会执行完整 Android 开机流程

**口述回答：** 先明确设备状态。已开机时，主要是供电状态变化，经硬件/内核及系统电池服务等路径反映到系统状态，应用通过受平台规则约束的电量或电源广播观察；这不是重新执行 Zygote 与 SystemServer 启动。关机插电可能进入厂商的充电模式，也可能开机，取决于硬件、bootloader 与产品配置。正常按键开机才按引导程序、内核、init、运行时/系统服务、桌面的主线继续分析。

**原理与边界：** “插电”不等于“正在给电池充电”，还受电量、温度和充电策略影响。应用看见的广播也不是硬件事件到达的精确时钟；ACTION_BATTERY_CHANGED 与电源连接广播有各自注册和投递规则。若面试官要讲到具体 HAL、驱动或关机充电 UI，应先限定 AOSP/厂商版本，再沿源码或 trace 查证，不能编造所有设备共用的一条函数链。

**追问：应用收到电源连接后能在 onReceive 直接长期上传吗？答：** 不合适。接收器的执行窗口和后台限制都有限，短处理后按需求交给合适的调度机制；充电约束下的可延迟工作可评估 WorkManager，不能依赖 Receiver 保活。

**易错点：** 用应用冷启动解释整个系统启动；宣称插电必然开机；把用户手机的厂商充电界面当成 AOSP 固定实现。

**官方参考：** [AOSP Bootloader 职责](https://source.android.com/docs/core/bootloader)；[Android 广播及其投递边界](https://developer.android.com/develop/background-work/background-tasks/broadcasts)；[电量与充电状态 API](https://developer.android.com/reference/android/os/BatteryManager)。系统开机主线见 [Q083](../questions/12-Framework与系统/Q083-Android-开机到应用可用的主要阶段是什么.md)。

<a id="ad14"></a>
### AD14 P1 高频传感器、实时图像与长时间日志，怎样设计有界的数据处理链

**口述回答：** 先给每类数据定义可丢失性和时延要求：页面展示通常只需最新快照；需要追溯的采样数据要带时间戳和序号，后台批量落盘；操作指令则要有 ID、执行结果和超时语义。回调只做最少的数据复制和入队，重计算、磁盘和网络移到明确的工作执行器；队列、缓冲区、日志和磁盘总量都设上限。不能用无限队列把“主线程不卡”换成几小时后的 OOM。

**原理与边界：** 这是对截图中宽泛设备场景的设计练习，不是某机器人产品的已验证实现。采样率是请求值，实际送达率要由时间戳测量；传感器的事件对象/数组不要无归属地保存到异步任务。UI 可限频或保留最新值，必须完整保存的数据则需要背压、降级或显式丢失标记；debounce 遇到持续输入可能一直不发，不能直接当固定周期采样。图像限制分辨率、并发和在途缓冲数量；日志轮转并设保留上限。所有策略都要结合低端设备的 CPU、内存、存储和热状态实测。

**追问：队列容量设 64 是否就安全？答：** 不足以证明；还要估算每项字节数、生产/消费速率、最坏阻塞时间，规定满队列时行为，并监测深度、延迟和丢弃量。指令入队成功不等于硬件执行成功，不能把 UI 展示的最新值策略套到不可丢的控制命令上。

**易错点：** 每个传感器事件开一个线程；误以为 SharedFlow/Channel 天然限制整条链路的内存，或不设日志上限；后台服务等于不会被杀；不了解驱动协议却虚构 JNI/HAL 调用细节。

**官方参考：** [传感器回调、采样与注册释放](https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview)；[Channel 缓冲与溢出策略](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/)；[Flow 限流语义对照 KT35](kotlin-coroutines-interview-guide.md#kt35)。前台服务、权限、ANR 与泄漏分别沿 [平台指南 AD18—AD23](android-platform-interview-guide.md#ad18)、[AD31—AD36](android-platform-interview-guide.md#ad31) 深入，不把这些通用方案说成自己的经历。

<a id="ad15"></a>
### AD15 P0 点击图标到 Activity 显示经历什么，主线程 Looper 需要自己初始化吗

**口述回答：** 先区分冷、温、热启动。以无应用进程的冷启动为例：Launcher 发起目标 Activity 的启动请求，系统解析组件和任务关系，必要时创建应用进程；应用运行时建立主线程执行环境并与系统关联，创建 Application，再按调度创建/启动 Activity、建立窗口和 View 树，完成首帧。已有进程或任务实例可能走复用路径，不应每次都从 fork 和 Application.onCreate 开始背。

**原理与边界：** AOSP 的 ActivityThread.main 中由框架调用 Looper.prepareMainLooper，然后 attach 并进入 Looper.loop；业务 Activity.onCreate 中不需要再 prepare/loop。子线程若要 Handler，应显式绑定可用 Looper，或选 HandlerThread。Application.onCreate 也不等于进程内第一段业务代码，组件初始化和 ContentProvider 可能更早参与。首帧显示与页面数据准备完成不同，要分别用启动 trace 和可交互指标定位。

**追问：既然主线程在 loop，为什么还能收到界面事件？答：** loop 正是持续取出并处理消息的事件循环，空闲时可以等待；真正的响应风险是单个任务、锁或同步 IPC 长时间占住处理机会。普通点击启动也不会重新启动整套 Android 系统。

**易错点：** 把 ActivityThread 当成每个 Activity 新建的工作线程；主线程再次调用 prepare；把“没有 Activity”推成“没有主 Looper”；把首帧耗时归因于唯一一条固定函数链。

**官方参考：** [Android 冷、温、热启动与首帧](https://developer.android.com/topic/performance/issues/launch-time)；[AOSP ActivityThread.main 官方镜像源码](https://github.com/aosp-mirror/platform_frameworks_base/blob/master/core/java/android/app/ActivityThread.java)。源码主分支不是所有设备版本的实现承诺，排障要固定版本。

## 已有题目的复习导航

| 本批线索 | 继续阅读与回答边界 |
| --- | --- |
| MVVM 层次、MVC/MVP 对比、重构 | [Q066](../questions/10-Jetpack架构与存储/Q066-MVC、MVP、MVVM-如何划分职责.md)、[手册 C04—C05](android-interview-handbook.md#q-c04)；ViewModel 不应持有 Activity/View，MVVM 不要求“双向持有对象”，Data Binding 双向表达式也不是架构定义 |
| 配置重建、ViewModelStoreOwner | [Q068](../questions/10-Jetpack架构与存储/Q068-ViewModel-为什么能跨配置变化保留状态.md)、[平台 AD01—AD02](android-platform-interview-guide.md#ad01)；ViewModel 跨配置变化复用，不跨进程死亡，Activity 内部保留路径应按 AndroidX 版本阅读 |
| ViewModel 的值为什么不能直接 get | [KT32](kotlin-coroutines-interview-guide.md#kt32)、[平台 AD03](android-platform-interview-guide.md#ad03)；原问题上下文不足。StateFlow.value 可读当前快照，却不建立订阅；LiveData.value 可能为 null；Compose 还取决于是否使用可观察状态，不能回答成“所有 ViewModel 都禁止 get” |
| Flow、冷热流、StateFlow/SharedFlow、取消 | [E015](../supplements/06-Kotlin与协程/E015-StateFlow-与-SharedFlow-怎么选择.md)、[KT22](kotlin-coroutines-interview-guide.md#kt22)、[KT30—KT38](kotlin-coroutines-interview-guide.md#kt30)；观察者是解释视角，Flow 还带挂起、取消和背压语义；并非所有 suspend 都检查取消 |
| LiveData 生命周期 | [Q069](../questions/10-Jetpack架构与存储/Q069-LiveData-如何做到生命周期感知.md)、[XML Q05](word-crush-android-xml-guide.md#q05)；STARTED/RESUMED 接收更新，observeForever 要主动释放，postValue 可能合并 |
| IPC、AIDL、Binder 数据限制 | [Q015](../questions/02-Handler线程与IPC/Q015-Binder-如何完成一次跨进程调用.md)、[平台 AD11—AD14](android-platform-interview-guide.md#ad11)；Binder 事务缓冲区约 1 MiB，由进程在途事务共享，不是每次调用都能安全传 1 MiB |
| Handler、子线程、Looper 等待与唤醒 | [Q009](../questions/02-Handler线程与IPC/Q009-Handler、Looper-和-MessageQueue-如何协作.md)、[Q012](../questions/02-Handler线程与IPC/Q012-Looper-队列空闲时为什么不会一直占用-CPU.md)、[平台 AD08—AD10](android-platform-interview-guide.md#ad08)；绑定哪个 Looper 决定执行线程，等待消息本身不是 ANR |
| 下载、Service、后台存活 | [平台 AD18—AD21](android-platform-interview-guide.md#ad18)、[XML Q31—Q32](word-crush-android-xml-guide.md#q31)；组件与线程分开，后台任务按实时性和持久性选调度，不宣称 Service 永久保活 |
| 启动模式、A→B→A、点击图标冷启动 | [Q002](../questions/01-Android基础与生命周期/Q002-Activity-切换与返回时的生命周期如何变化.md)、[Q003](../questions/01-Android基础与生命周期/Q003-Activity-启动模式与-onNewIntent-如何配合.md)、[本篇 AD15](#ad15)、[平台 AD32](android-platform-interview-guide.md#ad32)；先限定页面透明性、finish/返回、实例复用与进程是否存在 |
| RecyclerView 复用、外部引用泄漏、View 卡顿、低端机 | [平台 AD29—AD35](android-platform-interview-guide.md#ad29)、[Q075](../questions/11-性能与稳定性/Q075-怎样定位-Handler-导致的页面泄漏.md)、[Q116](../questions/16-工程设计与项目追问/Q116-多机型兼容问题应怎样建立验证矩阵.md)；用引用链、trace 与测试矩阵讲证据，不仅背优化开关 |
| ContentProvider 与存储 | [Q070](../questions/10-Jetpack架构与存储/Q070-SharedPreferences、数据库各适合什么数据.md)、[手册 C25](android-interview-handbook.md#q-c25)；Provider 是受权限控制的数据访问/共享抽象，底层可以是库、文件或其他源，不是与数据库并列的存储引擎 |
| 广播注册、动态权限、机器人硬件、多屏、组件化 | [平台 AD20—AD23](android-platform-interview-guide.md#ad20)、[AD36](android-platform-interview-guide.md#ad36)、[Q114](../questions/16-工程设计与项目追问/Q114-组件化的边界和通信协议怎样设计.md)；实际广播 action、导出标记、targetSdk、硬件接口和多屏产品需求需要先明确 |

**广播注册补充：** Manifest 声明和运行时 registerReceiver 有不同生命周期与隐式广播限制。动态注册选择最小需要范围并在不再需要时注销；按发送方、目标平台/API 规则与权限选择导出标记，不能一律使用 EXPORTED 或 NOT_EXPORTED。`onReceive` 不能用于长期阻塞工作。外部或高权限应用发出的广播，还需区分其是否来自系统 UID。参考[官方广播指南](https://developer.android.com/develop/background-work/background-tasks/broadcasts)。

**常用布局补充：** View 体系的 LinearLayout 表达线性排列，FrameLayout 常用于叠放，ConstraintLayout 表达约束；列表选择 RecyclerView，避免一次创建大量 item。Compose 的 Row/Column/Box 则以声明式组合表达类似布局需求，长列表使用 Lazy 容器。熟悉布局不等于深层嵌套更好，应按实际测量、布局成本和可访问性评估，沿 [XML Q07—Q09](word-crush-android-xml-guide.md#q07) 与 [Q027 View/Compose 对照](../questions/05-JetpackCompose/Q027-Compose-与-XML-View-的区别及选型依据.md) 学习不同布局模型，不混成同一套 API。

**设备与源码准备边界：** 新闻 App、智能音量、机器人权限或多屏等场景先问需求、设备能力、采样/时延和业务边界；算法团队接口、模型来源及具体 JNI/驱动调用没有资料，不编实现。JNI 资源边界可读 [JA39](java-core-interview-guide.md#ja39)，设备适配沿 Q116 建矩阵。源码导读时按“入口→状态拥有者→异步/错误出口→持久化→验证”演示，第三方接口故障时准备脱敏的本地替身和失败路径，不把离线假数据说成线上成功。

导航用于复用已有内容，不表示所链答案的全部追问都在这批面试出现。截图中“三级数据源”“MVP 模板代码”等残缺线索留在覆盖清单待澄清，不补造三级名称或模板实现。
