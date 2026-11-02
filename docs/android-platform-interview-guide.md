# Android 平台机制与故障场景面试问答

核对日期：2026-11-01。本文整理 **40 道编辑性练习**：AD01—AD25 为基础必会，AD26—AD40 为进阶追问。重点是“页面退出、进程死亡、权限变化或并发失败后会怎样”，不重复只背术语的定义题。

**证据与版本边界：** 回答依据 Android Developers、AOSP 和 Kotlin 官方资料组织，是通用原理、设计建议与待执行的验证方案，不是新增公司真题、作者个人经历、现有项目实现证明或测试通过记录。没有编译本文片段，也没有执行真机、弱网、性能或安全测试。涉及行为变化时同时区分设备系统版本与 `targetSdk`；列出的 API 31、33、34 等门槛只服务于对应场景，并非全部新版本变更清单。实际使用前仍须核对项目 AndroidX 依赖和目标设备。

**使用方式：** 先用 30—60 秒说完“处理方案、为什么、一个边界”，再回答追问。链接到旧题用于补定义；链接到 FeedLine、Word Crush 的内容须遵守各篇固定源码版本与静态阅读限制，不能把本篇建议说成项目已经采用。

## 基础必会（AD01—AD25）

<a id="ad01"></a>
### AD01 P0 旋转后页面正常，后台回来却空白，应怎样设计恢复链路

**口述回答：** 先区分配置变化和进程死亡。相同作用域的 ViewModel 可以跨配置变化保留状态，但进程被系统回收后它也消失。页面恢复应靠轻量状态记录查询词、选中项 ID、必要导航参数，再由 Repository 从数据库或网络重建内容。不能要求整个列表、网络连接和旧协程原样复活。

**原理与边界：** 已保存实例状态是恢复 UI 的线索，不是长期业务数据库；用户结束页面或任务后的重新进入，也不能默认沿用旧任务的恢复状态。

**追问与回答：** 只把列表缓存到单例能解决吗？不能；单例也属于进程内存。应保存足够重建页面的标识，持久业务数据另外落盘，并显示加载、空态和失败态。

**常见误区：** 把“不保留活动”测试通过等同于进程死亡恢复通过。

**官方依据：** [保存 UI 状态](https://developer.android.com/topic/libraries/architecture/saving-states)、[ViewModel](https://developer.android.com/topic/libraries/architecture/viewmodel)。**衔接：** [Q068](../questions/10-Jetpack架构与存储/Q068-ViewModel-为什么能跨配置变化保留状态.md)、[原手册 C21](android-interview-handbook.md#q-c21)。

<a id="ad02"></a>
### AD02 P0 SavedStateHandle 写入后，为什么仍不能承诺强停和重启都恢复

**口述回答：** SavedStateHandle 连接的是宿主的已保存状态机制，适合筛选条件、草稿 ID 等小状态。它可帮助恢复系统触发的进程死亡，但不是每次 `set` 都同步写磁盘；状态依附任务栈，强行停止、用户移除任务等结束任务的场景不能承诺恢复。需要跨任务、重启或长期保留的草稿，应保存到数据库或文件。

**原理与边界：** 官方特别说明：宿主已经停止后新增的写入，若没有再次经历 `onStart`、`onStop`，不会自动获得一次新的保存检查点。大对象还会增加序列化和 Binder 负担。

**追问与回答：** 保存一整个帖子对象还是帖子 ID？优先 ID 和少量用户输入；内容从可信数据源重建，并处理记录已删除或版本已变化。

**常见误区：** 将 SavedStateHandle 当成 Room，或说“进程死亡时系统一定先调用保存回调”。

**官方依据：** [SavedStateHandle 的恢复条件与限制](https://developer.android.com/topic/libraries/architecture/views/viewmodel/viewmodel-savedstate-views)。**衔接：** [AD01](#ad01)、[原手册 C09](android-interview-handbook.md#q-c09)。

<a id="ad03"></a>
### AD03 P0 页面不可见后 Flow 还在更新，lifecycleScope 为什么没有自动暂停

**口述回答：** `lifecycleScope.launch { collect(...) }` 通常到 owner 销毁才取消，不会因为进入 STOPPED 自动停止收集。可见 UI 用 `repeatOnLifecycle(STARTED)` 管理：到达状态时启动块，低于状态时取消块，回来再启动。Compose 显示状态可使用 `collectAsStateWithLifecycle`，但它不替代业务层自身的资源管理。

**原理与边界：** 取消收集不必然停止热流生产者；还要看 `stateIn/shareIn` 的作用域与 SharingStarted 策略。重新订阅冷流也可能重新发请求。

**追问与回答：** 在 repeat 块内依次 collect 两个长期流？第一个通常不返回，第二个无法开始；分别 `launch`，并明确异常与取消传播。

**常见误区：** 把 `launchWhenStarted` 的挂起行为当成完全等价的上游取消。

**官方依据：** [Views 的生命周期感知收集](https://developer.android.com/topic/libraries/architecture/views/coroutines-views)、[Compose 收集方式](https://developer.android.com/topic/libraries/architecture/coroutines)。**衔接：** [原手册 C18](android-interview-handbook.md#q-c18)、[FeedLine 收集方式核对](feedline-android-deep-dive.md#52-当前收集方式需要准确描述)。

<a id="ad04"></a>
### AD04 P0 Fragment 还在返回栈，为什么旧 binding 和监听必须释放

**口述回答：** Fragment 对象可能仍在，而它的 View 已在 `onDestroyView` 销毁。更新控件的观察应绑定 `viewLifecycleOwner`，在 View 创建后注册；binding、适配器回调和观察者不能继续持有旧 View。再次返回时面对的是新 View，不能复用旧 binding。

**原理与边界：** Fragment 生命周期和 View 生命周期不同；一个只会在 Fragment 最终销毁时取消的收集器，可能在没有 View 时收到数据。仅将字段设空，也不会自动注销外部注册的监听。

**追问与回答：** ViewModel 里保留 binding 是否方便？它的寿命可能长于 View，会泄漏或误更新旧界面；ViewModel 应暴露数据和事件，View 在自身生命周期内解释它们。

**常见误区：** 认为返回栈中的 Fragment 必然一直保留其 View。

**官方依据：** [Fragment 与 View 的生命周期](https://developer.android.com/guide/fragments/lifecycle)。**衔接：** [Q004](../questions/01-Android基础与生命周期/Q004-Fragment-为什么有两套生命周期.md)、[Word Crush Q02](word-crush-android-xml-guide.md#q02)。

<a id="ad05"></a>
### AD05 P0 编辑草稿只在 onDestroy 保存，为什么线上仍会丢内容

**口述回答：** 进程被系统结束时不保证收到 `onDestroy`，因此不能把它当成最后一次可靠提交。重要草稿应在明确业务动作或适当的去抖检查点持久化；页面状态恢复只保存草稿 ID、光标等小状态。保存过程要能表达进行中、成功或失败，不能点了保存就假定磁盘已经完成。

**原理与边界：** 去抖降低写入频率，却留下最后一段未写入窗口；需要按产品要求选择即时保存或显式提交。UI 生命周期回调可以触发补存，但不能提供断电一致性保证。

**追问与回答：** 每次输入都在主线程同步写文件？会引入卡顿；应将持久化封装为异步业务操作，并用版本号避免旧保存结果覆盖新内容。

**常见误区：** 将“退出前调用了函数”当成持久化成功证据。

**官方依据：** [Activity 生命周期中的进程终止](https://developer.android.com/guide/components/activities/activity-lifecycle)、[保存 UI 状态的选型](https://developer.android.com/topic/libraries/architecture/views/saving-states-views)。**衔接：** [原手册 C21](android-interview-handbook.md#q-c21)、[Word Crush Q03](word-crush-android-xml-guide.md#q03)。

<a id="ad06"></a>
### AD06 P0 相机返回时 Activity 已重建，怎样避免回调错位或业务上下文丢失

**口述回答：** 使用 Activity Result API，把回调注册与发起操作分开，每次创建都无条件按相同顺序注册。系统可能在结果返回前销毁进程，回调之外还要保存这次操作的业务标识、输出 URI 等必要上下文；结果到达后重新验证状态，而不是依赖旧页面字段。

**原理与边界：** 注册应在宿主创建前完成，launcher 至少到 CREATED 才能发起。回调重建机制不等于相机一定成功，也不替我们保存所有业务状态。

**追问与回答：** 把注册写在按钮点击里呢？不合适；注册时机会晚于要求，还可能在不同重建路径形成不同的注册顺序。按钮只负责 launch。

**常见误区：** 收到非空 URI 就认为文件完整、可读且可长期访问。

**官方依据：** [Activity Result 注册、顺序和独立保存状态](https://developer.android.com/training/basics/intents/result)。**衔接：** [原手册 C47](android-interview-handbook.md#q-c47)、[Word Crush 媒体与生命周期](word-crush-android-xml-guide.md#q29)。

<a id="ad07"></a>
### AD07 P0 长生命周期对象需要 Context，为什么不能全部替换成 Application

**口述回答：** 先看操作是否需要 Activity 的窗口、主题或生命周期。长期缓存 Activity 会让页面难以回收；进程级、无需界面的操作可以用合适的 Application context。但弹窗和主题化 UI 仍需要匹配的界面环境，不能靠替换 context 逃避所有权设计。更好的做法是缩短引用寿命或把 UI 操作留给页面。

**原理与边界：** 生命周期不匹配才是问题核心；Application 单例若通过监听器间接持有 View，照样可能泄漏。注册与注销必须成对设计。

**追问与回答：** WeakReference 可以代替注销吗？不能；它不停止后台工作，也不提供业务取消或回调顺序保证，最多减少某条强引用。

**常见误区：** 只检查匿名 Handler，忽略单例、监听表和运行中任务的引用链。

**官方依据：** [ViewModel 生命周期与引用约束](https://developer.android.com/topic/libraries/architecture/viewmodel)、[管理应用内存](https://developer.android.com/topic/performance/memory)。**衔接：** [Q074](../questions/11-性能与稳定性/Q074-内存泄漏与-OOM-是什么关系.md)、[Q075](../questions/11-性能与稳定性/Q075-怎样定位-Handler-导致的页面泄漏.md)。

<a id="ad08"></a>
### AD08 P0 postDelayed 返回 true，为什么倒计时仍会迟到甚至永不执行

**口述回答：** true 只表示消息成功入队，不表示已执行。Handler 依附的线程可能被长任务占用，Looper 也可能退出。延迟以 uptime 为时间基准，深度睡眠会增加墙上时钟看到的延迟。倒计时应保存截止时刻并在刷新时重新计算剩余时间，而不是把每次回调当成准确的一秒。

**原理与边界：** 若需要包含休眠的相对时长可考虑 `elapsedRealtime`；若要求跨进程存活或到点唤醒，应重新选择系统调度机制，不是延长 Handler 生命周期。

**追问与回答：** 页面退出后任务已开始，removeCallbacks 能停它吗？不能中断已运行回调；还要用任务版本或取消标记，执行前核对目标是否仍有效。

**常见误区：** 把入队成功、定时到期和业务完成混成一个状态。

**官方依据：** [Handler 的延迟、返回值与移除语义](https://developer.android.com/reference/android/os/Handler)、[SystemClock 时间基准](https://developer.android.com/reference/android/os/SystemClock)。**衔接：** [Q010](../questions/02-Handler线程与IPC/Q010-postDelayed-为什么不保证准时执行.md)、[Word Crush Q37](word-crush-android-xml-guide.md#q37)。

<a id="ad09"></a>
### AD09 P1 主线程消息被屏障推迟，改成异步 Handler 就能解决卡顿吗

**口述回答：** 异步 Handler 的消息不受同步屏障阻挡，但仍由同一个 Looper 线程执行。它不能打断正在运行的长回调，也不会把工作搬到后台。先确定延迟来自屏障、主线程计算、锁还是 Binder 等待，再决定是否存在合法的异步消息需求；普通业务不应靠绕开调度顺序抢占 UI 工作。

**原理与边界：** `Handler.createAsync` 是 API 28 起的公开接口；同一异步 Handler 内有顺序保证，与其他 Handler 的相对顺序则不能简单照搬同步队列假设。

**追问与回答：** 直接调用隐藏屏障接口呢？不应依赖隐藏 API 或手工操纵主线程屏障；更可靠的是缩短关键路径、分离阻塞工作并测量。

**常见误区：** 把这里的“异步”解释成新线程或无优先级限制的紧急通道。

**官方依据：** [Handler.createAsync](https://developer.android.com/reference/android/os/Handler#createAsync(android.os.Looper))。**衔接：** [Q011](../questions/02-Handler线程与IPC/Q011-同步屏障怎样影响主线程消息执行.md)、[AD31](#ad31)。

<a id="ad10"></a>
### AD10 P1 关闭 HandlerThread 时怎样处理已排队、正在运行和迟到结果

**口述回答：** 关闭是状态转换，不是只调用 quit。先拒绝新任务，决定是否处理已经到期的任务，再停止 Looper，清理回调和外部资源。`quitSafely` 会处理已经到期的消息，但丢弃尚未到期的延迟消息；它也不会强行中断当前回调。结果回到页面前还需核对任务身份。

**原理与边界：** `quitSafely` 从 API 18 提供。业务关闭完成、线程退出和网络资源关闭应分别确认；若需要等待线程结束，不能在主线程无期限 join。

**追问与回答：** 每种任务都新建一个 HandlerThread？通常成本过高；除非需要 Looper 接口或特定线程亲和性，可考虑执行器或结构化协程，并明确串行、并发和取消契约。

**常见误区：** 以为“安全退出”会等待所有未来定时任务完成。

**官方依据：** [HandlerThread 的退出及替代方案](https://developer.android.com/reference/android/os/HandlerThread)。**衔接：** [Q014](../questions/02-Handler线程与IPC/Q014-HandlerThread-与普通-Thread-有何差别.md)、[AD08](#ad08)。

<a id="ad11"></a>
### AD11 P0 同步 IPC 调用写成普通方法，为什么也可能把主线程卡住

**口述回答：** 同步远程调用会让调用线程等待服务端结果，跨进程不会自动替客户端切线程。即使业务参数很小，服务端排队、磁盘、锁或再次发起 IPC 都可能让等待变长。UI 应通过异步业务接口观察结果，并限制并发、处理超时与服务不可用。

**原理与边界：** `oneway` 只改变远程调用的等待方式，不代表业务完成；同进程本地调用加 oneway 也不会自动变成异步。超时不一定能取消对端已开始的工作。

**追问与回答：** 只给调用套 withTimeout 就万事大吉？不是；它能否及时取消取决于底层是否配合。还要设计请求 ID、过期结果处理，以及重复提交的业务语义。

**常见误区：** 认为 AIDL 服务端在 Binder 线程池执行，客户端主线程就不会等待。

**官方依据：** [AIDL 的调用与 oneway 语义](https://developer.android.com/develop/background-work/services/aidl)。**衔接：** [Q015](../questions/02-Handler线程与IPC/Q015-Binder-如何完成一次跨进程调用.md)、[原手册 C32](android-interview-handbook.md#q-c32)。

<a id="ad12"></a>
### AD12 P1 Binder 回调会在哪个线程执行，为什么持锁回调容易死锁

**口述回答：** 远程调用可能由 Binder 线程池并发处理，本地调用则可能直接在调用者线程执行，因此服务端和客户端回调都不能想当然当成主线程。跨进程调用还能产生嵌套重入：持锁调用对端，对端再回调回来，可能死锁或破坏正在迭代的数据。应在锁内复制必要状态，锁外调用外部代码。

**原理与边界：** 单个 Binder 线程也不等于没有重入；增加线程池大小不能修复错误的锁和状态契约。需要更新 UI 时显式切回 UI 所属线程。

**追问与回答：** oneway 就消除了并发风险？没有；它不让共享对象自动线程安全，也不能保证所有来源的业务回调顺序。

**常见误区：** 把“串行入口”当成“从入口到所有异步完成阶段都串行”。

**官方依据：** [AOSP Binder 线程与重入、死锁](https://source.android.com/docs/core/architecture/ipc/binder-threading)。**衔接：** [Word Crush Q34](word-crush-android-xml-guide.md#q34)、[AD11](#ad11)。

<a id="ad13"></a>
### AD13 P0 Bitmap 不到一兆也发生 TransactionTooLarge，应怎样定位与恢复

**口述回答：** Binder 事务缓冲区是进程中进行中事务共享的有限空间，官方当前说明约 1 MB，不是每个参数各有一个一兆额度。Intent、保存状态、请求和返回值都可能参与压力。应避免传大 Bitmap 或整列表，改传小标识、受控 URI 或文件描述符，并约束分页结果大小。

**原理与边界：** 这个异常不能让客户端判断是请求没送出，还是服务已处理但响应送不回；应视作可能部分失败，不能直接认定“操作未执行”。

**追问与回答：** 原样重试一次支付或写入可以吗？不安全；应使用业务幂等键和查询结果接口，先消解执行结果的不确定性。参数大小优化不等于幂等性。

**常见误区：** 用“单笔少于 1 MB”作为永不失败的保证。

**官方依据：** [TransactionTooLargeException 的共享缓冲与部分失败](https://developer.android.com/reference/android/os/TransactionTooLargeException)。**衔接：** [Q016](../questions/02-Handler线程与IPC/Q016-为什么大数据不应直接塞进-Binder-事务.md)、[AD02](#ad02)。

<a id="ad14"></a>
### AD14 P1 绑定的远程服务死亡后，客户端怎样恢复而不重复执行业务

**口述回答：** 连接状态要区分未连接、连接中、可用和已失效。收到断连或 Binder 死亡信号后，先使旧代理失效，处理等待中的请求，再按受控策略重连；新连接建立后重新注册必要回调。不能把旧代理仍非空等同于服务可用，也不能无条件重放所有未收到结果的操作。

**原理与边界：** 死亡通知和一次调用可能竞态；一次健康检查通过不保证下一次调用成功。具体恢复还要区分 `onServiceDisconnected`、绑定失效及显式解绑等回调语义。

**追问与回答：** 重连后如何补任务？只自动重试可安全重复的读操作，写操作使用请求 ID、结果查询或幂等协议；界面显示“结果待确认”，避免虚构失败或成功。

**常见误区：** 无限立即重连，或者重连后继续复用旧回调集合和旧任务世代。

**官方依据：** [绑定服务生命周期](https://developer.android.com/develop/background-work/services/bound-services)、[IBinder.DeathRecipient](https://developer.android.com/reference/android/os/IBinder.DeathRecipient)。**衔接：** [Q015](../questions/02-Handler线程与IPC/Q015-Binder-如何完成一次跨进程调用.md)、[AD13](#ad13)。

<a id="ad15"></a>
### AD15 P0 子控件已经收到 DOWN，父容器中途拦截时应该清理什么

**口述回答：** 当父容器在手势中途决定拦截，原本处理手势的子 View 会收到 CANCEL，随后事件交给父容器。子控件应像异常终止一样清理按压态、拖拽状态、长按任务和速度跟踪资源，不能把 CANCEL 当成 UP 触发点击或提交操作。

**原理与边界：** 拦截决定应结合方向、距离阈值和业务状态；`requestDisallowInterceptTouchEvent` 是手势协作请求，不是解决所有嵌套滚动问题的通用开关。

**追问与回答：** 为什么滑动后按钮还像按住一样？常见原因是只在 UP 清状态而遗漏 CANCEL；也要检查多指切换与窗口失去触摸目标的路径。

**常见误区：** 在所有 MOVE 都强制禁止父容器拦截，导致父级纵向滚动无法工作。

**官方依据：** [ViewGroup 拦截与 ACTION_CANCEL](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)。**衔接：** [Q020](../questions/03-View绘制与触摸/Q020-父容器中途拦截手势时子-View-会发生什么.md)、[Word Crush Q10](word-crush-android-xml-guide.md#q10)。

<a id="ad16"></a>
### AD16 P0 自定义 View 的 wrap_content 铺满屏幕，应怎样修正测量契约

**口述回答：** 先计算内容期望尺寸，加上 padding，并考虑建议最小尺寸，再结合父级 MeasureSpec 约束得到最终尺寸。EXACTLY 要服从确定尺寸，AT_MOST 不能超过上限，UNSPECIFIED 也不代表可以忽略自身内容。不要把 MeasureSpec 的整数值直接当像素宽高。

**原理与边界：** 测量决定需要多少空间，实际布局由父级决定。文本、图片、字体缩放和不同布局参数都会改变期望值，不能只验证一个固定父布局。

**追问与回答：** 在 onDraw 里读取完文字才 setMeasuredDimension？阶段不合适；应在测量阶段决定尺寸，绘制阶段使用已确定的几何信息。必要的尺寸缓存随内容和约束失效。

**常见误区：** 将 wrap_content 固定解释成某个 dp 值，忽略父容器上限。

**官方依据：** [自定义 View 的测量、尺寸与绘制](https://developer.android.com/develop/ui/views/layout/custom-views/custom-drawing)。**衔接：** [Q017](../questions/03-View绘制与触摸/Q017-View-的-measure、layout、draw-分别做什么.md)、[Q022](../questions/03-View绘制与触摸/Q022-自定义-View-怎样兼顾正确测量与绘制性能.md)。

<a id="ad17"></a>
### AD17 P0 修改自定义 View 属性后，何时要 requestLayout，何时只需 invalidate

**口述回答：** 看属性是否影响期望尺寸或布局。只改变颜色、进度等视觉内容，通常请求重绘；文字长度、内边距等影响测量结果时，还要请求布局。两者都是安排后续遍历，不是立即同步完成绘制；连续变化应避免每次都制造不必要的全树布局工作。

**原理与边界：** 布局与绘制请求可能被系统合并，但不能因此在绘制回调里无条件发起新布局，形成反复遍历。跨线程修改 View 状态仍需遵守 UI 线程约束。

**追问与回答：** `invalidate` 后截图仍是旧值怎么办？先确认状态是否在正确线程更新、控件是否可见，以及截图是否等待了实际绘制；不要把调用返回当成帧已显示。

**常见误区：** 认为 requestLayout 必定立即重绘整个屏幕，或者 invalidate 必定重新测量。

**官方依据：** [优化自定义 View 与减少无谓布局](https://developer.android.com/develop/ui/views/layout/custom-views/optimizing-view)。**衔接：** [Q018](../questions/03-View绘制与触摸/Q018-requestLayout-与-invalidate-有何区别.md)、[AD33](#ad33)。

<a id="ad18"></a>
### AD18 P0 把上传放进 Service 后仍卡 UI，组件与线程应怎样分工

**口述回答：** Service 是组件，不是后台线程；默认生命周期回调仍在所在进程主线程。需要另外选择协程、执行器等执行耗时工作，再根据任务是否可延后、是否要跨进程存活、用户是否可感知，选择 WorkManager、前台服务或页面内任务。创建组件本身不提供无限运行保证。

**原理与边界：** 普通协程和线程随进程结束消失；前台服务也有启动、类型和运行限制。上传协议还需定义断线重试、取消和恢复信息。

**追问与回答：** Activity 销毁就应停止所有上传吗？取决于所有权：临时预览可以取消，用户明确提交且应继续的上传需要独立于页面的业务任务状态，而不是偷偷延长页面引用。

**常见误区：** 把“应用不在前台”“后台线程”“后台 Service”当成同一个维度。

**官方依据：** [Service 默认线程与使用场景](https://developer.android.com/develop/background-work/services)、[后台工作选型](https://developer.android.com/develop/background-work)。**衔接：** [Q007](../questions/01-Android基础与生命周期/Q007-Activity-和-Service-有什么区别.md)、[AD19](#ad19)。

<a id="ad19"></a>
### AD19 P0 每天八点提醒和最终完成上传，为什么不能套同一种 WorkManager 配置

**口述回答：** WorkManager 适合满足约束后需要可靠调度的持久工作，不承诺某个钟点精确执行；周期工作会受约束和系统优化影响。上传可以设计为受网络条件约束、允许重试的工作。用户明确要求准确时刻的提醒，应评估 AlarmManager 的合适闹钟类型和权限，而不是把周期间隔当成闹钟时间。

**原理与边界：** 精确闹钟有资源成本与权限限制。Android 14 上，多数新安装且 target 33+ 的应用不再默认获得 SCHEDULE_EXACT_ALARM；应检查能力并提供合理降级，不能假定安装即授权。

**追问与回答：** unique work 是否等于服务端只执行一次？不等于；它控制本地同名工作的排队策略，业务写入仍要有幂等键与状态核对。

**常见误区：** 用最短周期或 expedited 标记声称“准点且立即执行”。

**官方依据：** [工作请求的时间和周期约束](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work)、[闹钟选型](https://developer.android.com/develop/background-work/services/alarms)、[Android 14 精确闹钟变化](https://developer.android.com/about/versions/14/behavior-changes-all#schedule-exact-alarms)。**衔接：** [Q008](../questions/01-Android基础与生命周期/Q008-如何设计每天固定时间提醒.md)、[AD38](#ad38)。

<a id="ad20"></a>
### AD20 P0 权限已经允许，为什么后台启动定位或录音前台服务仍会失败

**口述回答：** 要分别检查后台启动资格、前台服务类型声明、类型对应权限，以及资源权限当前是否可用。Android 12 的 target 31+ 后台启动限制存在特定例外；这不等于取得例外后就能使用所有资源。Android 14、target 34+ 对需要 while-in-use 权限的服务在创建时检查，后台拿着“使用期间允许”并不等于正在允许使用。

**原理与边界：** target 34+ 还需按类型声明相应前台服务权限并满足运行前提。`checkSelfPermission` 返回 GRANTED，仍可能只代表“在使用期间授权”，不是后台启动许可。不同类型及更新版本还有额外限制。

**追问与回答：** 用普通广播收到事件后直接启动能绕过吗？不能；必须逐项核对该入口是否属于官方例外、用户意图及资源权限，失败要有可解释的恢复入口。

**常见误区：** 把所有 SecurityException 都归因于忘记写一条 uses-permission。

**官方依据：** [后台启动与 while-in-use 限制](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start)、[Android 14 前台服务类型要求](https://developer.android.com/about/versions/14/changes/fgs-types-required)。**衔接：** [AD18](#ad18)、[AD21](#ad21)。

<a id="ad21"></a>
### AD21 P0 用户拒绝通知权限后，前台服务还能启动吗，提示又在哪里

**口述回答：** Android 13 引入通知运行时权限，但启动前台服务本身不以 POST_NOTIFICATIONS 获准为前提；应用仍必须按要求提供服务通知，其他前台服务限制也仍有效。用户拒绝后，相关提示通常不出现在通知抽屉，但前台服务任务管理界面仍有提示，不能将拒绝理解为服务静默无限运行的授权。

**原理与边界：** target 33+ 的应用可以自己选择合适的请求时机；较低 target 的系统触发时机不同。还要区分通知权限、通知渠道设置及少数豁免通知。

**追问与回答：** 为了保证任务完成能强迫用户开通知吗？不能；解释用户可感知的收益，处理拒绝并提供任务状态入口，不能把权限拒绝当成业务一定未开始。

**常见误区：** 认为拒绝通知权限会自动停止全部前台服务。

**官方依据：** [通知运行时权限与前台服务](https://developer.android.com/develop/ui/compose/notifications/notification-permission)、[Android 13 的提示位置变化](https://developer.android.com/about/versions/13/behavior-changes-13#notification-permission-fgs-appearance)。**衔接：** [AD20](#ad20)。

<a id="ad22"></a>
### AD22 P0 只让用户选一张图片，为什么不应先申请整个媒体库权限

**口述回答：** 选择少量图片优先评估系统 Photo Picker，让用户授予所选媒体的访问，而不是默认索取整个媒体库。真正需要自建全库浏览时再按系统版本和用途申请对应权限。在 Android 14 上，尤其迁移到 target 34+ 的自建媒体库选择器，必须处理“只允许部分照片”的访问状态；实际行为还与权限声明及兼容模式有关。查询结果可能不完整，不能把没有读到解释为用户没有照片。

**原理与边界：** Photo Picker 的可用性取决于设备及支持组件，可通过相应 Activity Result contract 处理兼容回退。自建选择器的部分访问与系统 Picker 是两种不同方案，不要混为同一个权限弹窗。

**追问与回答：** 进程恢复后仍可用旧媒体列表吗？需要重新核对权限与 URI 访问，处理用户重新选择、撤销和文件删除，而不是永远相信缓存。

**常见误区：** 为选择一张头像申请 READ_MEDIA_IMAGES 后，假定获得全部图片永久访问权。

**官方依据：** [Photo Picker](https://developer.android.com/training/data-storage/shared/photo-picker)、[Android 14 部分照片访问](https://developer.android.com/about/versions/14/changes/partial-photo-video-access)。**衔接：** [原手册 C47](android-interview-handbook.md#q-c47)、[FeedLine A15](feedline-android-deep-dive.md#a15-为什么选图不需要申请整个相册权限)。

<a id="ad23"></a>
### AD23 P0 content URI 今天能读，明天失败，应检查授权还是转换真实路径

**口述回答：** URI 是提供者的访问标识，不保证对应可读取的本地文件路径，云端文档更不能靠“转真实路径”解决。应通过 ContentResolver 打开流或描述符，检查授权寿命、提供者状态和文件是否仍存在。需要长期访问时，只有支持且确实授予可持久授权的结果才能请求保留；否则按需求复制到应用管理的存储。

**原理与边界：** 调用 `takePersistableUriPermission` 不能把任意临时 URI 变成永久权限；授权存在也不保证文件未被删除、移动或提供者始终在线。

**追问与回答：** 返回缓存路径就代表复制成功？不代表；要处理流打开、分块读写、空间不足、取消和失败清理，只有完成提交后才能发布可用结果。

**常见误区：** 把 URI 字符串当成本地路径，或者复制未完成就向后续上传宣布成功。

**官方依据：** [Storage Access Framework 与持久 URI 授权](https://developer.android.com/training/data-storage/shared/documents-files)、[Photo Picker 的访问保留](https://developer.android.com/training/data-storage/shared/photo-picker#persist-media-file-access)。**衔接：** [原手册 C48](android-interview-handbook.md#q-c48)、[FeedLine A16](feedline-android-deep-dive.md#a16-copyuritolocalcache-返回了路径就代表保存成功吗)。

<a id="ad24"></a>
### AD24 P0 两次 Room 查询之间数据变了，suspend 为什么没有提供事务保证

**口述回答：** suspend 表达可挂起，不代表多步数据库操作原子执行。若业务要求“读状态、校验、修改”看到一致关系，应将必要操作放入合适事务，或用带条件的原子 SQL 更新并检查影响行数。Room 支持异步 DAO，普通磁盘或 JSON 工作仍需自己安排合适执行位置。

**原理与边界：** 事务保护指定数据库操作，不能让一个远端网络调用也加入 SQLite 原子提交。数据库 Flow 重新发射也不是“每条业务事件恰好一次”的通知机制。具体事务 API 需对应项目使用的 Room 版本，不能混用不同版本示例。

**追问与回答：** 在事务里等待网络返回再提交？会扩大占用和失败窗口；通常先取得必要结果，再用短事务校验版本并落库，冲突时显式重试或提示。

**常见误区：** 把单线程执行器、suspend 或两个连续 DAO 调用都等同于事务。

**官方依据：** [异步 DAO 查询](https://developer.android.com/training/data-storage/room/async-queries)、[Room Transaction](https://developer.android.com/reference/androidx/room/Transaction)。**衔接：** [Q072](../questions/10-Jetpack架构与存储/Q072-Room-怎样表达一对多关系与联合查询.md)、[Word Crush Q20](word-crush-android-xml-guide.md#q20)。

<a id="ad25"></a>
### AD25 P0 偏好设置计数并发丢更新，换成异步写入为什么仍不够

**口述回答：** 问题是“读取旧值再写新值”是否处于同一原子更新边界，而不只是有没有阻塞线程。SharedPreferences 的 apply 异步落盘不让外部读改写自动原子化，commit 同步也不解决整段业务竞态。DataStore 提供事务式更新，应在同一次 update/edit 中读取当前值并写新值，避免拿外部旧快照计算。

**原理与边界：** 同一文件不能随意创建多个 DataStore 实例；跨进程应按官方要求选择多进程实现与一致配置，不能混用单进程和多进程访问。复杂关联数据仍更适合数据库。

**追问与回答：** commit 返回成功就能跨进程直接共享偏好吗？不能；写入返回值与跨进程一致性是不同契约，SharedPreferences 不是通用跨进程存储协议。

**常见误区：** 把“异步更快”作为存储正确性结论。

**官方依据：** [DataStore 原子更新与多进程要求](https://developer.android.com/topic/libraries/architecture/datastore)、[SharedPreferences.Editor](https://developer.android.com/reference/android/content/SharedPreferences.Editor)。**衔接：** [Q071](../questions/10-Jetpack架构与存储/Q071-SharedPreferences-的多线程与多进程限制是什么.md)、[原手册 C25](android-interview-handbook.md#q-c25)。

## 进阶追问（AD26—AD40）

<a id="ad26"></a>
### AD26 P1 Compose 的 LaunchedEffect 没重启，为什么回调却读到旧值

**口述回答：** Effect 的 key 决定何时取消旧工作并重启，不是把所有捕获值都自动刷新。若变化代表任务身份改变，应作为 key；若任务应继续，只需使用最新回调，可用 rememberUpdatedState 提供当前值。先解释“哪些变化应重启、哪些只是更新参数”，再选择 API。

**原理与边界：** Effect 离开组合时会被取消，但底层非协作操作或外部注册仍需正确清理；需要注册监听并注销时考虑 DisposableEffect。固定 key 不是“永远只运行一次”的跨页面承诺。

**追问与回答：** 把所有状态都塞进 key 呢？可能频繁取消重启请求、重复注册或丢失进行中工作；key 应表达真实任务身份，而不是为了消除旧值随意扩大范围。

**常见误区：** 在 Composable 主体直接发请求，依靠“应该不会重组”控制次数。

**官方依据：** [Compose Effect 的 key、取消与最新值](https://developer.android.com/develop/ui/compose/side-effects)。**衔接：** [原手册 C12](android-interview-handbook.md#q-c12)、[FeedLine 副作用边界](feedline-android-deep-dive.md#4-compose-怎样把状态变化变成界面变化)。

<a id="ad27"></a>
### AD27 P1 Compose 列表重排后输入串到别的项，保存状态与业务身份怎样配合

**口述回答：** 列表项状态要跟随稳定业务身份，而不是当前位置。稳定 key 有助于框架识别项目，输入状态还应放在恰当所有者中；需要重建恢复的小状态选择可保存表示，需要长期保留的内容落入持久层。key、remember 和保存恢复解决不同问题，不能互相替代。

**原理与边界：** remember 只是组合内记忆；rememberSaveable 受已保存状态类型、体积和恢复条件限制，不应保存整个大列表。稳定 key 也不会阻止所有重组或自动发现普通可变集合的修改。

**追问与回答：** 每次随机生成 UUID 当 key？身份每次都变，反而破坏复用与状态关联；应选稳定、唯一且符合当前保存机制要求的业务键。

**常见误区：** 通过标注 Stable 或使用 key，掩盖原地修改可变对象的状态通知问题。

**官方依据：** [Compose 状态保存](https://developer.android.com/develop/ui/compose/state-saving)、[列表 key 与状态](https://developer.android.com/develop/ui/compose/lists#item-keys)。**衔接：** [原手册 C09](android-interview-handbook.md#q-c09)、[C10](android-interview-handbook.md#q-c10)。

<a id="ad28"></a>
### AD28 P1 支付结果用 SharedFlow 发一次，为什么旋转或后台切换后仍会漏提示

**口述回答：** 先把可靠业务结果与瞬时提示分开。没有订阅者且 replay 为零时，SharedFlow 不是可靠事件日志；加 replay 又可能让新订阅者重复收到。支付结果应进入可恢复业务状态，UI 从状态推导展示，再按业务键确认处理。Toast 一类允许丢失的提示才可以采用较轻的事件策略。

**原理与边界：** extraBufferCapacity 不等于无人订阅时永久保存。Channel 也有取消、接收后尚未完成处理和进程死亡窗口，不会自动提供业务“恰好一次”。

**追问与回答：** 把事件清空就不会重复了吗？清空本身也可能与重建竞态；应明确谁拥有待处理状态、何时确认、重建如何恢复，并让关键动作幂等。

**常见误区：** 只用“StateFlow 表状态、SharedFlow 表事件”一句口诀替代交付契约。

**官方依据：** [StateFlow 与 SharedFlow](https://developer.android.com/kotlin/flow/stateflow-and-sharedflow)、[SharedFlow 无订阅者时的缓冲语义](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)。**衔接：** [原手册 C17](android-interview-handbook.md#q-c17)、[FeedLine A05](feedline-android-deep-dive.md#a05-为什么-sharedflow-发出了事件仍可能没提示)。

<a id="ad29"></a>
### AD29 P1 RecyclerView 的 DiffUtil 已算出变化，为什么界面仍可能不对

**口述回答：** DiffUtil 需要可比较的旧新快照；若把同一对象原地改完再提交，旧数据也已变，差异可能无法正确识别。还要分别实现业务身份和可见内容比较，payload 只能优化局部绑定，完整绑定必须能恢复最终状态。点击时按当前有效位置取数据或使用稳定业务标识，避免捕获旧 position。

**原理与边界：** payload 可能被合并或在 View 未附着时丢弃，所以不能把业务状态只藏在某次局部绑定里。异步差异计算也需要明确最新列表和回调的对应关系。

**追问与回答：** areItemsTheSame 相同就跳过绑定？不对；身份相同只表示同一业务项，还要比较展示内容。反过来只比较标题也会把不同业务对象误当同一项。

**常见误区：** 以为 ListAdapter 会替我们冻结所有嵌套可变对象。

**官方依据：** [DiffUtil 的不可变快照要求](https://developer.android.com/reference/androidx/recyclerview/widget/DiffUtil)、[Adapter payload 与位置](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView.Adapter)。**衔接：** [Word Crush Q14](word-crush-android-xml-guide.md#q14)、[Q15](word-crush-android-xml-guide.md#q15)。

<a id="ad30"></a>
### AD30 P1 View 嵌套滚动卡住，把所有触摸事件交给子控件为什么不是完整解法

**口述回答：** 先区分手势由谁处理，与已经产生的滚动距离由父子如何协商。触摸拦截决定事件目标，nested scrolling 则传递预消费、已消费和未消费距离；二者不是一回事。还要检查测量约束、同轴嵌套、滚动边界和 fling，避免为了消除抢手势而让父容器完全失去滚动能力。

**原理与边界：** 统一采用兼容的嵌套滚动父子协议；自定义组件要正确报告消费距离，不能声称“已经消费全部”却没有改变位置。测量导致子列表一次展开全部项时，也不能仅靠触摸开关修复性能。

**追问与回答：** 如何验证修复？分别测试上下边界、斜向拖动、快速 fling、取消和不同高度约束，并记录谁消费了多少距离；单次手指慢滑正常不足以证明契约正确。

**常见误区：** 把 `nestedScrollingEnabled=false` 当成所有组合下的固定答案。

**官方依据：** [触摸拦截](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)、[NestedScrollingChild3 的消费距离](https://developer.android.com/reference/androidx/core/view/NestedScrollingChild3)。**衔接：** [Q026](../questions/04-RecyclerView/Q026-嵌套-RecyclerView-的滑动冲突怎么处理.md)、[AD15](#ad15)。

<a id="ad31"></a>
### AD31 P1 ANR 栈停在 Binder 或锁等待，为什么不能只优化栈顶方法

**口述回答：** 栈顶只说明采样时正在做什么，不一定是根因。若主线程等待 Binder，要追服务端线程、排队与锁；若在等锁，要找持锁线程及它正在等待的资源。结合 ANR 类型、发生时间、全线程栈和系统 trace 建立因果链，再缩短主线程关键路径或消除锁与 IPC 依赖。

**原理与边界：** 不同 ANR 类型有不同触发条件，不能把所有情况简化成同一个“五秒规则”。抓到的栈也可能晚于真正阻塞阶段，需要多种证据互相印证。

**追问与回答：** 把入口改成协程就修复了吗？不一定；默认仍可能在主线程执行，同步 Binder 和锁等待也可能不可取消。应确认实际线程、等待关系和修复后的时序。

**常见误区：** 看到栈里有系统类就认定系统问题，或者只降低主线程函数代码行数。

**官方依据：** [按类型诊断 ANR 与 Binder、锁阻塞](https://developer.android.com/topic/performance/anrs/diagnose-and-fix-anrs)。**衔接：** [Q077](../questions/11-性能与稳定性/Q077-ANR-常见成因与排查流程是什么.md)、[AD11](#ad11)。

<a id="ad32"></a>
### AD32 P1 冷启动首帧变快了，为什么仍不能直接宣布用户可用时间改善

**口述回答：** 先定义指标：初始显示时间与完整显示时间不同。把加载移到首帧之后可能缩短首帧，却延长用户真正能使用内容的等待。用一致设备、构建类型、数据和启动状态做多次 Macrobenchmark，观察分布和 trace；把 reportFullyDrawn 放在真实完成关键内容的时刻，而不是为了指标提前调用。

**原理与边界：** 冷、温、热启动不能混为一组；debug 构建、后台资源竞争和网络波动会影响对比。Baseline Profile 可降低部分代码执行成本，不会自动移除业务 I/O 与依赖串行。

**追问与回答：** 删除一个 900 ms 定时器就提升 900 ms？不能这样推导；还要看它是否位于测量关键路径，并提供可复核的前后测量。

**常见误区：** 用一次手工秒表或代码里的延迟常量充当性能收益。

**官方依据：** [启动时间与 TTID、TTFD](https://developer.android.com/topic/performance/issues/launch-time)、[Macrobenchmark](https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview)。**衔接：** [Q078](../questions/11-性能与稳定性/Q078-应用启动优化怎样区分首帧与可交互时间.md)、[原手册 P02](android-interview-handbook.md#q-p02)。

<a id="ad33"></a>
### AD33 P1 列表滚动掉帧，怎样判断是布局、图片、主线程还是渲染压力

**口述回答：** 先固定可复现操作与设备刷新率，观察慢帧并记录系统 trace，再看主线程、RenderThread、调度、图片解码和 I/O 是否占用帧关键路径。JankStats 可以关联帧与页面状态，帮助定位哪类交互受影响；修复应针对观测到的瓶颈，然后用同场景复测，而不是先增加缓存或随处加边界组件。

**原理与边界：** 16.7 ms 只是 60 Hz 的帧间隔示意，不能作为所有设备统一预算；重组次数少也不等于布局、绘制或 GPU 成本低。等待网络导致内容空缺，也不一定属于帧调度掉帧。

**追问与回答：** 为什么缓存变大反而更卡？可能增加内存压力和 GC，或缓存失效成本更高；需同时比较帧耗时、内存和命中情况，不能只看命中率。

**常见误区：** 把“看起来流畅”写成已证明性能提升。

**官方依据：** [JankStats](https://developer.android.com/topic/performance/jankstats)、[设备系统 trace](https://developer.android.com/topic/performance/tracing/on-device)。**衔接：** [Q076](../questions/11-性能与稳定性/Q076-列表滚动掉帧应怎样定位.md)、[FeedLine A06](feedline-android-deep-dive.md#a06-stable-key-为什么不能保证只有点赞项重组)。

<a id="ad34"></a>
### AD34 P1 图片文件只有几百 KB，为什么列表加载后内存会增加几十 MB

**口述回答：** 压缩文件大小不等于解码后的像素占用。以普通 ARGB_8888 为估算，宽乘高再乘每像素四字节，一张大图就可能占很多内存；还要考虑解码临时对象、缓存、多个尺寸版本和显示资源。应按目标尺寸解码、限制并发与缓存，并用工具确认实际占用。

**原理与边界：** 这个公式是特定格式的估算，不代表所有 Bitmap 配置或底层分配；现代 Android 中像素存储、硬件位图等还有不同内存路径。不能只看 Java 对象本身的浅大小。

**追问与回答：** 主动 recycle 所有离屏图片？不能随意回收仍被其他消费者使用的对象；先确认库的所有权与资源管理契约，避免显示失败或重复解码。

**常见误区：** 用 JPEG 大小估算图片内存，或者把缓存上限设成“越大越好”。

**官方依据：** [Bitmap 内存与 Android 版本差异](https://developer.android.com/topic/performance/graphics/manage-memory)、[高效加载大位图](https://developer.android.com/topic/performance/graphics/load-bitmap)。**衔接：** [Q079](../questions/11-性能与稳定性/Q079-Bitmap-的内存占用怎样估算.md)、[原手册 C14](android-interview-handbook.md#q-c14)。

<a id="ad35"></a>
### AD35 P1 Java 堆看起来不大仍被杀，怎样区分泄漏、峰值和系统内存压力

**口述回答：** 先区分异常日志中的 OOM 与系统因内存压力结束进程，再分开看 Java/Kotlin 堆、native、图形资源等占用。泄漏是超出预期生命周期仍被引用，短时分配峰值也能导致失败但不一定是泄漏。用同一操作反复进入退出，结合堆转储引用链、进程内存统计和系统记录判断，而不是只截一张堆曲线。

**原理与边界：** PSS、RSS 和对象堆大小含义不同，不能相加或互换；Java 堆转储也不能完整说明所有 native、共享和图形内存来源。系统杀进程不一定产生 Java OOM 堆栈。

**追问与回答：** 调大 largeHeap 就算修复？不是；可能仅推迟失败，且不修复无界缓存、泄漏或峰值复制。应减少长期保留和并发峰值，再评估真实业务容量。

**常见误区：** 认为有 GC 就不会泄漏，或将所有被杀都归因于某一张 Bitmap。

**官方依据：** [内存管理概览](https://developer.android.com/topic/performance/memory-overview)、[内存问题测量](https://developer.android.com/topic/performance/measuring-performance)。**衔接：** [Q074](../questions/11-性能与稳定性/Q074-内存泄漏与-OOM-是什么关系.md)、[AD34](#ad34)。

<a id="ad36"></a>
### AD36 P1 权限上次已允许，这次访问资源为什么仍应检查并处理失败

**口述回答：** 权限是会变化的运行环境，不是安装后永久配置。用户可以撤销，部分权限具有一次性或使用期间语义，系统也有未使用应用权限重置等机制。应在执行功能前检查当前能力，在恰当时机解释并申请，同时处理检查与实际调用之间的变化、权限不足和资源不可用，提供可用的降级路径。

**原理与边界：** 检查通过不保证资源一定成功，例如服务占用、URI 失效或前台服务使用期间限制仍可能存在。不要将权限结果永远缓存为 true。

**追问与回答：** shouldShowRequestPermissionRationale 为 false 就一定永久拒绝？不能独立这样判断；首次请求前也可能为 false，应结合是否已请求过和当前权限状态，避免无限弹窗或自动跳设置。

**常见误区：** 启动即索取所有权限，或者拒绝一个可选权限就让整个应用功能无法使用。

**官方依据：** [请求运行时权限与拒绝处理](https://developer.android.com/training/permissions/requesting)、[一次性权限与重置机制](https://developer.android.com/training/permissions/requesting#one-time)。**衔接：** [AD20](#ad20)、[AD22](#ad22)。

<a id="ad37"></a>
### AD37 P1 通知 PendingIntent 为什么优先不可变，目标组件又为什么要明确

**口述回答：** PendingIntent 是让其他主体代表创建应用执行预定义动作的系统令牌，设计时要限制动作和目标。一般通知点击优先显式指定组件并使用不可变形式；只有需要接收方填入信息的确切场景才考虑可变，并收窄可变范围。在 Android 12（API 31）及以上且 target 31+ 时，必须明确可变性，不能为了消除异常随便改成可变。

**原理与边界：** 可变性与 exported 是不同防线：不可变令牌不替代组件的访问控制和输入校验。需区分不同通知的业务身份，避免复用同一令牌导致跳转参数串用。

**追问与回答：** 已声明 exported=false 就绝对安全？不够；PendingIntent 可能授予代表应用调用的能力，仍要限制创建与分发对象，检查携带的业务参数和授权状态。

**常见误区：** 把 PendingIntent 当成普通 Intent 的延迟复制品，忽略其权限委托属性。

**官方依据：** [PendingIntent 风险与缓解](https://developer.android.com/privacy-and-security/risks/pending-intent)、[Android 12 可变性要求](https://developer.android.com/about/versions/12/behavior-changes-12#pending-intent-mutability)。**衔接：** [Q003](../questions/01-Android基础与生命周期/Q003-Activity-启动模式与-onNewIntent-如何配合.md)、[AD06](#ad06)。

<a id="ad38"></a>
### AD38 P1 数据已经提交服务器但本地任务被杀，恢复时怎样避免重复创建记录

**口述回答：** 这是结果不确定性，不是简单的“失败重试”。提交前为逻辑操作分配稳定业务 ID，并持久化待发送状态；服务端按该 ID 幂等处理或提供结果查询。恢复时根据本地状态和远端结果继续推进，成功确认后更新本地记录。WorkManager 可以帮助重新调度，但无法单独让网络与数据库形成一个原子事务。

**原理与边界：** 本地去重、HTTP 重试和服务器幂等是不同层次。取消本地 Worker 也不保证远端尚未提交；业务应允许“待确认”状态，不得盲目报告未执行。

**追问与回答：** 只用 unique work 就够吗？不够；它约束本地队列中的同名工作，不能阻止服务端已成功而客户端未记录时再次提交。业务幂等键应跨重试保持稳定。

**常见误区：** 每次重试生成新订单 ID，或成功回调到达前就删除恢复记录。

**官方依据：** [离线优先数据层与持久队列](https://developer.android.com/topic/architecture/data-layer/offline-first)、[WorkManager 唯一工作与状态管理](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/manage-work)。**衔接：** [原手册 N28](android-interview-handbook.md#q-n28)、[AD19](#ad19)。

<a id="ad39"></a>
### AD39 P1 单元测试、设备测试和 Compose 界面测试分别能证明什么

**口述回答：** 按风险分层：纯业务规则用本地单元测试快速覆盖；依赖系统行为、数据库或组件交互的部分用相应集成或设备测试；UI 测试验证交互与语义状态。测试用了 fake 就只能证明 fake 契约下的逻辑，不代表真实系统权限、Binder、厂商设备或性能都通过。性能还需要专门的测量方法。

**原理与边界：** Compose 的语义树断言不等同于像素完全正确；截图测试也不自动证明触摸、无障碍或后台恢复正确。测试代码存在与在明确环境执行通过，应分别记录。

**追问与回答：** 如何选一个高价值用例？例如控制 Repository 的完成顺序，验证页面重建后旧请求不会覆盖新请求，再补一个真实宿主恢复测试，而不是只断言按钮文字存在。

**常见误区：** 将所有测试数量相加当质量分数，或者把模拟器单次通过写成全部真机兼容。

**官方依据：** [Android 测试层次](https://developer.android.com/training/testing/fundamentals)、[Compose 测试语义](https://developer.android.com/develop/ui/compose/testing/semantics)。**衔接：** [原手册 C36](android-interview-handbook.md#q-c36)、[C39](android-interview-handbook.md#q-c39)。

<a id="ad40"></a>
### AD40 P1 怎样设计一组可复核的页面恢复测试，而不把旋转当作全部验证

**口述回答：** 把配置变化、页面 View 重建、后台系统进程回收和用户主动结束任务分开验证，并预先写清各场景应该保留什么。输入草稿、导航、滚动和进行中操作分别检查；恢复后还要验证重复请求、过期回调、权限变化和失败提示。记录系统、target、依赖、步骤与日志，才能判断结果适用于哪种条件。

**原理与边界：** “不保留活动”主要暴露 Activity 重建问题，不能等同于整个进程死亡。强行停止也不是系统后台回收的替身，任务栈与恢复语义不同；不能因此要求系统恢复被用户主动放弃的临时页面状态。

**追问与回答：** 保存状态测试工具通过就足够吗？不够；它能验证序列化与恢复逻辑，却不能覆盖所有真实任务调度、外部资源和厂商行为。应组合受控测试与目标环境复现，并明确未覆盖项。

**常见误区：** 只验证“页面重新打开没崩溃”，却没有断言数据、任务身份和资源归属正确。

**官方依据：** [UI 状态恢复的生命周期条件](https://developer.android.com/topic/libraries/architecture/saving-states)、[Compose 状态恢复测试](https://developer.android.com/develop/ui/compose/state-saving#verify-state-restoration)。**衔接：** [Q116](../questions/16-工程设计与项目追问/Q116-多机型兼容问题应怎样建立验证矩阵.md)、[AD01](#ad01)、[AD39](#ad39)。
