# Flutter 与 Dart 面试问答及 SSH Mobile 实践指南

核对日期：2026-11-01。本文面向 Android 开发实习面试，围绕 Flutter 的语言、界面、异步、性能和原生边界整理 **52 个问答与 6 个练习**。先理解机制，再结合 SSH Mobile 说明代码如何工作，不把背出术语当成已独立掌握实现。

**证据边界：** 通用原理参考本次查阅的 Flutter、Dart 官方文档与 Provider API 文档；项目例子固定到 `hejulian2004/ssh_mobile` 提交 `5aba1d83405d53bdabd3807c76139489d17d7e6a`，私有源码链接需要访问权限。通用推荐不代表项目已采用；静态源码阅读不等于真机测试、性能测量或安全审计。本次不修改应用源码，也不虚构提速数字或个人贡献。

现有 [Rust SDK 导读](sdk-source-deep-dive.md) 和 [QUIC 导读](quic-source-deep-dive.md) 继续负责底层网络细节；本篇重点回答 Flutter 面试官会如何沿着项目追问。

## 阅读顺序

- **P0 必会：** 先学 Q01—Q03、Q07—Q08、Q10、Q12—Q16、Q18—Q24、Q30—Q32、Q39—Q43。这些直接影响能否解释现有项目。
- **P1 深入：** 补路由、布局、文件、缓存、测试与工程配置。
- 每题先用一分钟回答“是什么、为什么、边界是什么”，再接受追问。没有实际做过的改进，明确说“可以这样验证”，不要说成“我已经优化”。

## 问题索引

- [Q01 P0 final const late 有什么区别](#q01)
- [Q02 P0 空安全解决了什么 为什么用了感叹号还会崩](#q02)
- [Q03 P0 相等性 hashCode 和不可变状态为什么相关](#q03)
- [Q04 P1 Dart 泛型和 Java 类型擦除一样吗](#q04)
- [Q05 P1 extends implements with 分别适合什么](#q05)
- [Q06 P1 extension 是否真的修改了原类](#q06)
- [Q07 P0 async await 会不会自动开后台线程](#q07)
- [Q08 P0 事件队列和微任务队列如何影响执行顺序](#q08)
- [Q09 P1 Future.wait 怎样处理并发任务和错误](#q09)
- [Q10 P0 timeout 取消和忽略结果有什么区别](#q10)
- [Q11 P0 Future 和 Stream 有什么区别 订阅怎样清理](#q11)
- [Q12 P0 Isolate 和线程有什么区别](#q12)
- [Q13 P1 SendPort 发送对象是不是都零拷贝](#q13)
- [Q14 P0 compute 在 Android 和 Web 上一样吗](#q14)
- [Q15 P0 Widget Element RenderObject 分别是什么](#q15)
- [Q16 P0 StatelessWidget 就不会重建吗 StatefulWidget 自己是可变的吗](#q16)
- [Q17 P0 Key 怎样影响复用 为什么列表不能乱用下标 Key](#q17)
- [Q18 P1 GlobalKey 为什么不能到处用](#q18)
- [Q19 P0 initState didChangeDependencies didUpdateWidget dispose 怎样分工](#q19)
- [Q20 P0 BuildContext 是什么 为什么有时找不到 Provider 或 Navigator](#q20)
- [Q21 P0 await 后检查 mounted 就足够了吗](#q21)
- [Q22 P0 setState 做了什么 为什么回调不能 async](#q22)
- [Q23 P0 FutureBuilder 为什么不能每次 build 都新建请求](#q23)
- [Q24 P0 Flutter 布局为什么说约束向下尺寸向上](#q24)
- [Q25 P0 Column 内 ListView 或 Expanded 为什么会报无限高度](#q25)
- [Q26 P1 ListView.builder Sliver 和 KeepAlive 分别解决什么](#q26)
- [Q27 P1 Flutter 一帧怎样从状态变化到屏幕](#q27)
- [Q28 P0 RepaintBoundary 能否阻止 build](#q28)
- [Q29 P1 Impeller 是什么 能否说 Flutter 已彻底没有卡顿](#q29)
- [Q30 P1 点击和滚动冲突为什么不能只看 onTap](#q30)
- [Q31 P0 ValueNotifier 为什么原地修改 List 不通知](#q31)
- [Q32 P0 Provider Consumer Selector 分别负责什么](#q32)
- [Q33 P1 何时用局部状态 何时用共享模型](#q33)
- [Q34 P0 页面 dispose 和应用进入后台是一回事吗](#q34)
- [Q35 P1 Navigator Router 和返回键应该怎样理解](#q35)
- [Q36 P1 保活 State 和进程死亡后的状态恢复有什么区别](#q36)
- [Q37 P0 为什么不能把每个网络 chunk 直接当 JSON](#q37)
- [Q38 P0 大文件为什么要流式读写](#q38)
- [Q39 P1 JSON 序列化为什么也可能卡 UI](#q39)
- [Q40 P0 MethodChannel EventChannel FFI 怎样选择](#q40)
- [Q41 P0 SSH Mobile 的 Rust FFI 是否所有工作都在后台 Isolate](#q41)
- [Q42 P0 跨 FFI 的内存和销毁顺序为什么危险](#q42)
- [Q43 P0 冷启动按需初始化怎样避免第一次并发调用重复创建](#q43)
- [Q44 P0 Flutter 卡顿从哪里开始排查](#q44)
- [Q45 P1 少 build 就一定更快吗 const 能完全阻止更新吗](#q45)
- [Q46 P0 Dart 有 GC 为什么还会内存泄漏](#q46)
- [Q47 P1 图片缓存为什么可能导致 OOM](#q47)
- [Q48 P0 单元测试 Widget 测试与集成测试分别证明什么](#q48)
- [Q49 P0 hot reload hot restart 和重新安装有什么区别](#q49)
- [Q50 P1 debug profile release 和 flavor 是一回事吗](#q50)
- [Q51 P0 Flutter 插件能否替代 Android 权限与生命周期知识](#q51)
- [Q52 P0 项目主要由 AI 辅助生成 面试如何证明 Flutter 能力](#q52)

## 一 Dart 语言基础

<a id="q01"></a>
### Q01 P0 final const late 有什么区别

**回答：** `final` 限制变量只能赋值一次，不保证所引用对象内部不可变。`const` 表示编译期常量，常量集合不能增删；`const` 构造函数允许在满足条件时创建常量对象，但不是每次调用都自动成为常量。`late` 把部分初始化检查推迟到运行时，可用于延迟初始化；未赋值就读取仍可能报错。

**追问：** `final List<int> xs = []; xs.add(1)` 为什么可以？变量绑定不变，集合内容仍可变。**易错：** 不用 `late` 掩盖“资源可能从未创建”的真实生命周期；用可空字段与显式状态往往更清晰。[Dart 变量](https://dart.dev/language/variables)

<a id="q02"></a>
### Q02 P0 空安全解决了什么 为什么用了感叹号还会崩

**回答：** 可空类型 `T?` 把“可能没有值”写进类型系统，要求调用方处理。`?.` 条件访问，`??` 提供空值替代，`!` 是开发者断言非空，不会把 null 变成有效对象。动态数据、反序列化和生命周期变化仍需要边界校验。

**追问：** `Object?` 和 `dynamic` 有何不同？前者可以承载任意值但操作受静态类型约束，后者放宽静态检查，错误可能留到运行时。**易错：** 不要把服务端 JSON 强转后加 `!` 当作校验。[空安全](https://dart.dev/null-safety/understanding-null-safety)

<a id="q03"></a>
### Q03 P0 相等性 hashCode 和不可变状态为什么相关

**回答：** `identical` 判断是否同一对象；`==` 可由类型定义值相等，默认对象实现以身份判断。重写 `==` 时必须保持相等对象拥有相同 `hashCode`。若用可变字段参与 hash，再把对象当 Map key 或放进 Set 后修改字段，可能破坏查询预期。

**追问：** 新建 List 是否代表列表内容一定变了？不代表；身份、内容相等和 UI 是否需要更新是不同问题。**易错：** 状态比较策略应与数据模型配套，不能只说“copy 一下就线程安全”。[Object 相等性](https://api.dart.dev/dart-core/Object/operator_equals.html)

<a id="q04"></a>
### Q04 P1 Dart 泛型和 Java 类型擦除一样吗

**回答：** Dart 泛型具有运行时类型信息，例如可进行 `value is List<String>` 这样的检查。泛型使容器、结果和接口保留类型约束，但从外部输入得到 `dynamic` 后仍要验证内容。类型转换并不负责把错误类型的数据自动转换成正确值。

**追问：** 为什么不全用 `List<dynamic>`？会丢失接口契约，错误在深层消费时才出现。**易错：** 不把 Dart 的运行时泛型机制直接等同于 Java 的擦除机制。[泛型](https://dart.dev/language/generics)

<a id="q05"></a>
### Q05 P1 extends implements with 分别适合什么

**回答：** `extends` 建立单继承关系并复用父类实现；`implements` 要求满足接口契约，不自动继承实现；`with` 应用 mixin 复用一组能力。mixin 可声明约束，多个 mixin 的方法组合也有顺序语义，需要看具体定义。

**追问：** 动画中为什么经常看到 ticker provider mixin？它提供与动画时钟相关的能力，而不是给业务对象随意增加继承层级。**易错：** mixin 不等于多继承任意多个普通类。[Mixins](https://dart.dev/language/mixins)

<a id="q06"></a>
### Q06 P1 extension 是否真的修改了原类

**回答：** 扩展方法提供调用语法上的便利，不会把方法动态加入原对象的实例结构；其解析依赖接收者的静态类型。静态类型是 `dynamic` 时，不能期待像普通成员一样自动找到某个 extension。

**追问：** 为什么相同对象换一个变量类型，扩展选择可能不同？因为扩展解析不是普通虚方法运行时派发。**易错：** 方便的扩展不要隐藏耗时、文件写入等不明显的副作用。[扩展方法](https://dart.dev/language/extension-methods)

## 二 异步 事件循环与 Isolate

<a id="q07"></a>
### Q07 P0 async await 会不会自动开后台线程

**回答：** 不会。`async` 让函数返回 Future，`await` 允许等待未完成结果时让出执行机会；当前 isolate 上的同步计算仍会占用它。一次异步网络请求之后的大 JSON 解析、同步文件读取或同步 FFI 调用，仍可能阻塞 UI isolate。

**追问：** 在函数外面加 `Future` 能否解决卡顿？只是改变调度时机，不自动改变执行位置。**项目联系：** SSH Mobile 的 native 命令提交与 helper isolate 轮询需分开解释，见 Q41。[Dart 并发模型](https://dart.dev/language/concurrency)

<a id="q08"></a>
### Q08 P0 事件队列和微任务队列如何影响执行顺序

**回答：** 先完成当前同步调用栈；排队的微任务会在后续普通异步事件前得到处理。持续递归添加微任务可能使 Timer、输入等事件迟迟得不到执行，所以微任务不是“越优先越好”的性能工具。

**追问：** `Future(() {})`、`Future.microtask`、已完成 Future 的后续处理是否全在同一队列？不能一概而论，要结合构造方式与 API 的调度规则分析。**易错：** 不把 `await` 的所有细节背成“必然新增一个普通事件”。[scheduleMicrotask](https://api.dart.dev/dart-async/scheduleMicrotask.html)

<a id="q09"></a>
### Q09 P1 Future.wait 怎样处理并发任务和错误

**回答：** 它等待传入的一组 Future，结果列表按输入顺序排列，不按完成顺序排列。一个任务失败会使聚合结果失败；`eagerError` 影响何时向外完成错误，不能当成自动取消其他任务。若每项都需要记录成功或失败，应设计逐项结果类型。

**追问：** 一百个文件同时启动读取合适吗？需要并发上限，`Future.wait` 本身不是限流器。**易错：** 聚合失败不代表之前的副作用都回滚了。[Future.wait](https://api.dart.dev/dart-async/Future/wait.html)

<a id="q10"></a>
### Q10 P0 timeout 取消和忽略结果有什么区别

**回答：** `Future.timeout` 控制等待结果的期限，原操作可能继续执行。取消需要底层支持，例如取消网络 Call、关闭订阅或发送取消命令；忽略迟到结果只防止它污染当前状态，不代表远端操作停止。

**追问：** 上传超时后直接重试为什么危险？服务器可能已完成，只是响应丢失；要先核对任务标识和最终状态。**项目联系：** SDK pending 超时、Rust 操作结束和业务成功是不同阶段。[Future.timeout](https://api.dart.dev/dart-async/Future/timeout.html)

<a id="q11"></a>
### Q11 P0 Future 和 Stream 有什么区别 订阅怎样清理

**回答：** Future 表达一次结果或错误；Stream 表达连续的数据、错误及结束事件。需要区分单订阅流和广播流，不能假设所有流都会为晚加入的订阅者重放历史。持有订阅的对象负责取消，并处理 cancel 的异步清理。

**追问：** 暂停消费是否一定暂停上游？取决于流和生产者；有些实现只在本地缓存。**易错：** 页面退出后不处理订阅，可能既浪费资源又让旧数据更新新页面。[Stream](https://api.dart.dev/dart-async/Stream-class.html)

<a id="q12"></a>
### Q12 P0 Isolate 和线程有什么区别

**回答：** Dart isolate 有独立的 Dart 对象堆与事件循环，通过消息通信，不像共享内存线程直接读写同一普通 Dart 对象。它适合把较重计算与 UI 分离，但创建、通信和数据传递都有成本。

**追问：** 还会不会有竞争？业务层仍有异步时序竞争，FFI 操作的外部原生资源也可能被多方访问。**易错：** “堆隔离”不等于跨语言 native handle 自动安全。[并发与 Isolate](https://dart.dev/language/concurrency)

<a id="q13"></a>
### Q13 P1 SendPort 发送对象是不是都零拷贝

**回答：** 不是。允许发送哪些对象、对象图如何复制与共享，取决于 isolate 的创建关系和对象类型。不可发送资源不能靠随意塞进 Map 绕过限制；闭包还可能捕获比预期更多的对象。大块字节可评估 TransferableTypedData，但也要计算创建和消费成本。

**追问：** 能直接发送 Socket、Controller 或任意 FFI 资源吗？先查消息可发送规则，不根据对象“看起来简单”判断。**易错：** 不把传指针地址等同于安全转移所有权。[SendPort.send](https://api.dart.dev/dart-isolate/SendPort/send.html)

<a id="q14"></a>
### Q14 P0 compute 在 Android 和 Web 上一样吗

**回答：** 当前 Flutter API 说明：原生平台的 compute 回调在另一个 isolate 执行；Web 上在当前事件循环执行。因此“用了 compute，所有平台都多核并行”是错误表述。传入回调、参数与结果也必须满足相关传递要求。

**追问：** 每收到一个小数据包就 compute 合适吗？调度与复制可能比计算更贵，高频任务可考虑持久 worker 与批量处理。**易错：** compute 不是通用后台保活服务。[compute](https://api.flutter.dev/flutter/foundation/compute.html)

## 三 Widget Element 状态与生命周期

<a id="q15"></a>
### Q15 P0 Widget Element RenderObject 分别是什么

**回答：** Widget 是界面配置；Element 是配置在树中的持久化实例与连接位置；RenderObject 负责布局、绘制等渲染工作。并非每个 Widget 都直接对应一个 RenderObject。刷新界面通常会产生新 Widget 配置，但可复用已有 Element 与渲染对象。

**追问：** 为什么 Flutter 可以频繁创建 Widget？配置对象与昂贵渲染资源的生命周期不同。**易错：** 不把三棵树理解成严格一一对应，也不把 Flutter Widget 等同 Android View 实例。[架构概览](https://docs.flutter.dev/resources/architectural-overview)

<a id="q16"></a>
### Q16 P0 StatelessWidget 就不会重建吗 StatefulWidget 自己是可变的吗

**回答：** StatelessWidget 也会因父级或依赖变化而重新 build。StatefulWidget 的配置仍是不可变的，可变数据通常放在关联的 State 或外部状态对象。是否使用 StatefulWidget，不由“界面会不会变化”这一个表面现象决定。

**追问：** 父级传入新配置时 State 一定重建吗？匹配更新时 State 可以保留，并通过 didUpdateWidget 接收变化。**易错：** 不为避免重建把所有页面写成 StatefulWidget。[State 生命周期](https://api.flutter.dev/flutter/widgets/State-class.html)

<a id="q17"></a>
### Q17 P0 Key 怎样影响复用 为什么列表不能乱用下标 Key

**回答：** 框架判断已有 Element 能否用新 Widget 更新，关键条件包括相同 runtimeType 与 key。列表重排时，稳定业务 ID 有助于状态跟随对应数据，而非误跟随原位置。下标只能表达位置，插入或删除后容易让输入框、动画等状态对应错误。

**追问：** 每次 build 都创建 UniqueKey 会怎样？容易把本应复用的子树当成新身份。**项目联系：** 终端历史改动曾处理动态 Key 与状态保留问题，不能只把 Key 当刷新开关。[Widget.canUpdate](https://api.flutter.dev/flutter/widgets/Widget/canUpdate.html)

<a id="q18"></a>
### Q18 P1 GlobalKey 为什么不能到处用

**回答：** GlobalKey 可标识全局唯一 Element、访问关联 State，并支持特定场景下重挂载子树。它不是“更高级的普通 Key”，可能触发较重的子树生命周期和依赖更新；应由长生命周期对象稳定持有，不在每次 build 临时重建。

**追问：** 为了跨组件调用方法必须用 GlobalKey 吗？可先考虑回调、Controller 或明确状态接口。**易错：** 同一棵应用树中重复使用同一个 GlobalKey 不是共享状态方案。[GlobalKey](https://api.flutter.dev/flutter/widgets/GlobalKey-class.html)

<a id="q19"></a>
### Q19 P0 initState didChangeDependencies didUpdateWidget dispose 怎样分工

**回答：** initState 做一次性初始化；依赖 InheritedWidget 的初始化和变化处理放在 didChangeDependencies；父级配置更新但复用 State 时，didUpdateWidget 负责更新绑定；dispose 释放自己拥有的资源。订阅对象变化时，应解绑旧对象再绑定新对象。

**追问：** deactivate 等于最终销毁吗？不等于，子树可能重新插入。**易错：** 不在 dispose 释放只是“借用”的全局 Runtime，也不假设每次进程终止都会完整执行 dispose。[State 生命周期](https://api.flutter.dev/flutter/widgets/State-class.html)

<a id="q20"></a>
### Q20 P0 BuildContext 是什么 为什么有时找不到 Provider 或 Navigator

**回答：** BuildContext 代表树中的位置，祖先查找基于这个位置。若使用的 context 位于 Provider 或 Navigator 之上，查询自然找不到目标；新建 Builder 获得子树中的 context 可以解决部分位置问题，但不能替代正确作用域设计。

**追问：** 能把 context 存进应用单例吗？容易延长页面引用并在失效后使用，应避免将 UI 位置对象变成业务依赖。**易错：** context 不是全局服务容器。[InheritedWidget](https://api.flutter.dev/flutter/widgets/InheritedWidget-class.html)

<a id="q21"></a>
### Q21 P0 await 后检查 mounted 就足够了吗

**回答：** mounted 只说明对应 State 或 context 仍在树中；它不保证当前请求仍是最新请求、服务器目标未变、页面可见或操作仍获批准。await 后除了检查生命周期，还可能需要比较 requestId、目标快照或取消标记。

**追问：** 页面仍 mounted，但用户从服务器 A 切到 B，A 的结果能显示吗？应按请求语义判定，不能仅靠 mounted。**易错：** 检查 mounted 不会自动取消网络请求。[BuildContext.mounted](https://api.flutter.dev/flutter/widgets/BuildContext/mounted.html)

<a id="q22"></a>
### Q22 P0 setState 做了什么 为什么回调不能 async

**回答：** setState 同步执行状态变更回调，并通知框架安排对应 State 的 build；它不是立刻把整屏画完。回调不能是 async，应在外部完成异步操作，再在仍有效时同步更新状态。耗时计算也不应藏进回调。

**追问：** 多次调用会不会立即画多帧？构建调度与调用次数不是简单一一对应，但多余通知和状态计算仍有成本。**易错：** setState 不等于强制整个应用重新布局与绘制。[setState](https://api.flutter.dev/flutter/widgets/State/setState.html)

<a id="q23"></a>
### Q23 P0 FutureBuilder 为什么不能每次 build 都新建请求

**回答：** build 可以多次发生，若构造 FutureBuilder 时顺便创建新请求，就可能反复启动操作。通常在 initState 或配置变化的明确位置取得 Future，并决定何时替换。还要区分首次加载、刷新中、旧数据、错误和空结果。

**追问：** 缓存 Future 后参数变化怎么办？在 didUpdateWidget 等合适位置根据参数变化重建请求，并防止旧结果覆盖。**易错：** FutureBuilder 不自动解决重试、去重或底层取消。[FutureBuilder](https://api.flutter.dev/flutter/widgets/FutureBuilder-class.html)

## 四 布局 输入与渲染

<a id="q24"></a>
### Q24 P0 Flutter 布局为什么说约束向下尺寸向上

**回答：** 父布局向子布局提供尺寸约束，子布局在约束内计算并返回自身大小，位置由父布局决定。所以写 width 100 不是向父级下达命令，紧约束可能让该请求没有效果。排查布局先看约束来源，再看子布局如何回应。

**追问：** tight 和 loose 有何区别？前者限定唯一尺寸，后者允许一定范围内选择。**易错：** 不用一层层随意加 Container 掩盖约束问题。[约束模型](https://docs.flutter.dev/ui/layout/constraints)

<a id="q25"></a>
### Q25 P0 Column 内 ListView 或 Expanded 为什么会报无限高度

**回答：** 滚动布局在滚动方向可能向子项提供无界约束；而需要“填满剩余高度”的 Expanded 必须知道有限的剩余空间。要先明确谁负责滚动、哪里提供有限高度，再选择 Expanded、有限 SizedBox 或统一 Sliver 结构。

**追问：** shrinkWrap 是否万能？它可能需要更多尺寸计算，长列表并非免费。**易错：** 不把 shrinkWrap 加到所有列表就宣布修复性能。[约束模型](https://docs.flutter.dev/ui/layout/constraints)

<a id="q26"></a>
### Q26 P1 ListView.builder Sliver 和 KeepAlive 分别解决什么

**回答：** builder 允许按需构建列表项；Sliver 参与滚动视口布局，可组合列表、网格和折叠头部；KeepAlive 保存特定子项状态，但会增加常驻对象。它们不自动分页网络数据，也不保证所有列表都无卡顿。

**追问：** 聊天消息离屏后是否全部保活？应按状态需求和内存预算取舍。**易错：** 不把惰性构建等同于 Android RecyclerView 原样复用机制，也不把固定 itemExtent 用于实际变高内容。[ListView](https://api.flutter.dev/flutter/widgets/ListView-class.html)

<a id="q27"></a>
### Q27 P1 Flutter 一帧怎样从状态变化到屏幕

**回答：** 可从状态通知、build 更新配置、布局计算几何、paint 生成绘制描述，再到合成与光栅化理解。哪些阶段执行取决于脏标记及变化内容，并非每个 Widget 更新都完整重跑所有阶段。语义信息还服务于无障碍，不只是视觉像素。

**追问：** build 很快但仍掉帧可能在哪里？布局、绘制、图片、光栅化和原生侧都可能有开销。**易错：** 不把“Dart 单 isolate”理解成整个引擎只有一个线程。[Flutter 架构](https://docs.flutter.dev/resources/architectural-overview)

<a id="q28"></a>
### Q28 P0 RepaintBoundary 能否阻止 build

**回答：** 不能。它在绘制层形成独立 display list 边界，适合更新频率不同的区域，可能减少重复记录绘制内容。它不阻止状态通知或 build，也不是保证缓存命中；额外边界会带来图层等成本。

**追问：** 包住整个长列表一定更快吗？必须对比实际帧时间与重绘区域。**易错：** 隔离 build 用合理状态范围，隔离 repaint 用绘制边界，两者责任不同。[RenderRepaintBoundary](https://api.flutter.dev/flutter/rendering/RenderRepaintBoundary-class.html)

<a id="q29"></a>
### Q29 P1 Impeller 是什么 能否说 Flutter 已彻底没有卡顿

**回答：** Impeller 是 Flutter 的渲染后端，目标之一是让着色器等工作更可预测。可用性和默认启用策略依赖平台、Flutter 版本与设备能力，应查项目实际运行信息，不能把某个平台的默认行为外推到全部平台。

**追问：** 换后端能解决同步 JSON 解析或数据库阻塞吗？不能，它们并不是同一类瓶颈。**易错：** 不把 Impeller 写成“无需性能分析”的理由。[Impeller](https://docs.flutter.dev/perf/impeller)

<a id="q30"></a>
### Q30 P1 点击和滚动冲突为什么不能只看 onTap

**回答：** 指针命中测试确定事件路径，手势识别器在 gesture arena 中竞争解释一次交互。嵌套点击、拖动和滚动会涉及不同识别器，命中行为与最终手势胜出不是同一件事。

**追问：** 改成 opaque 或 translucent 就能让父子都收到最终点击吗？不能据此保证，仍要看识别器竞争和回调语义。**易错：** 不直接套用 Android ViewGroup 拦截流程解释 Flutter。[手势机制](https://docs.flutter.dev/ui/interactivity/gestures)

## 五 状态管理 页面与恢复

<a id="q31"></a>
### Q31 P0 ValueNotifier 为什么原地修改 List 不通知

**回答：** ValueNotifier 通过给 value 赋值时的新旧相等性判断来通知，不会自动观察对象内部字段。原地 add 改变列表内容，但没有触发符合条件的 value 替换。可采用不可变快照赋新值，或由合适模型显式发通知。

**追问：** 谁 dispose notifier？创建并拥有它的对象，不是所有订阅者。**项目联系：** 聊天输入区用局部 ValueNotifier 管高频输入，详见后文源码例子。[ValueNotifier](https://api.flutter.dev/flutter/foundation/ValueNotifier-class.html)

<a id="q32"></a>
### Q32 P0 Provider Consumer Selector 分别负责什么

**回答：** Provider 提供实例及其作用域；Consumer 等组件订阅并构建；Selector 先提取需要的值，再按比较规则决定是否更新 builder。当前 Provider API 默认使用深集合比较，但项目具体行为仍要核对锁定版本和 shouldRebuild 配置。

**追问：** 返回同一个不断原地修改的对象安全吗？不安全，旧快照可能一起变化，比较就失去意义。**易错：** Selector 只能减少不相关订阅更新，不能修复业务竞态。[Selector](https://pub.dev/documentation/provider/latest/provider/Selector-class.html)

<a id="q33"></a>
### Q33 P1 何时用局部状态 何时用共享模型

**回答：** 输入草稿、局部展开等可从最小拥有者开始；跨页面业务状态、连接生命周期和持久数据需要明确的共享模型与资源管理。选择 Provider、Riverpod、Bloc 等应看依赖关系、测试和事件复杂度，不是包名越多越专业。

**追问：** SSH Mobile 是否全部使用 Riverpod 或 Bloc？本篇没有这样的代码依据；已核实例子是 Provider/Selector/ValueNotifier 与业务服务。**易错：** 不把状态框架代替架构，也不让页面随意销毁应用级连接。

<a id="q34"></a>
### Q34 P0 页面 dispose 和应用进入后台是一回事吗

**回答：** 不是。页面状态是否保留取决于路由和树结构；应用生命周期表示整个应用与宿主平台的关系。Flutter 的状态名也不与 Android 回调逐项同名对应。系统突然终止进程时，不应依赖收到完整的生命周期序列后才保存关键数据。

**追问：** 后台能否一直跑 Dart Timer 保活 SSH？不能当作平台承诺，后台限制和原生机制需要另行设计。**易错：** 页面不可见不等于已经 dispose。[AppLifecycleState](https://api.flutter.dev/flutter/dart-ui/AppLifecycleState.html)

<a id="q35"></a>
### Q35 P1 Navigator Router 和返回键应该怎样理解

**回答：** Navigator 管理路由栈；Router 适合将路由状态、URL 或深链与页面集合协调。嵌套 Navigator 要明确返回操作针对哪一层。返回拦截还要适应系统手势，当前 PopScope 通过 canPop 等机制表达可返回性，并报告尝试结果。

**追问：** 弹窗后用错 context 为什么可能 pop 错层？context 对应的 Navigator 可能不是目标。**易错：** 不直接套用过时的返回拦截模板；API 能否使用看项目版本。[路由](https://docs.flutter.dev/ui/navigation) · [PopScope](https://api.flutter.dev/flutter/widgets/PopScope-class.html)

<a id="q36"></a>
### Q36 P1 保活 State 和进程死亡后的状态恢复有什么区别

**回答：** 保活只在当前进程和对应对象存续条件下有意义；进程死亡需要可恢复的数据。RestorationMixin 等机制要求登记可恢复属性，不会自动保存任意 Controller、Socket 或 native handle。复杂业务仍应保存轻量标识并重新加载。

**追问：** 恢复到某个终端页就等于 SSH 会话已重连吗？不等于，UI 恢复和连接恢复是两条流程。**易错：** 不把页面截图或内存缓存当持久化方案。[RestorationMixin](https://api.flutter.dev/flutter/widgets/RestorationMixin-mixin.html)

## 六 网络 文件与平台边界

<a id="q37"></a>
### Q37 P0 为什么不能把每个网络 chunk 直接当 JSON

**回答：** 网络分块是传输层提供数据的节奏，不保证与业务消息边界一致。一次 JSON、UTF-8 字符或 SSE 事件可能跨多个块，一个块也可能包含多个事件。应逐层处理字节解码、分帧和业务解析，并限制缓存大小。

**追问：** 刚收到半个事件就断网怎么办？保留不完整与已完成事件的区别，按协议决定报错或重试。**项目联系：** Agent 流式回复不能把“收到字节”直接等同于一条模型消息。此题是协议设计原理，不代表所有异常场景都已实测。

<a id="q38"></a>
### Q38 P0 大文件为什么要流式读写

**回答：** 整文件预加载让内存需求随文件大小增长；分块读取并等待下游消费可控制业务缓冲规模。还要处理文件句柄、取消、失败清理和写入完成，不能只把 readAsBytes 换成 Stream 就宣布峰值内存固定。

**追问：** 上游读取很快、网络很慢怎么办？需要背压或有界队列，避免每块都启动未等待的 Future。**项目联系：** 历史 SFTP 优化与 Rust 文件协议是不同链路，不能混用块大小。[File.openRead](https://api.dart.dev/dart-io/File/openRead.html)

<a id="q39"></a>
### Q39 P1 JSON 序列化为什么也可能卡 UI

**回答：** 网络读取异步不代表解析异步。同步解析、模型构造和大量列表转换可能消耗 UI isolate 时间。可用小样本测量后决定是否下沉，且要考虑传递对象的成本。代码生成有助于类型映射维护，不自动校验所有业务规则。

**追问：** 字段不存在、类型变化和版本兼容怎么处理？定义必需字段、默认值与错误策略，不把全部失败吞成空列表。**易错：** 不把 Gson 的反射方案直接套到 Dart。[JSON 与序列化](https://docs.flutter.dev/data-and-backend/serialization/json)

<a id="q40"></a>
### Q40 P0 MethodChannel EventChannel FFI 怎样选择

**回答：** MethodChannel 适合平台方法请求与结果；EventChannel 适合由平台侧提供事件流；FFI 通过 C ABI 调用原生库函数。平台通道常用于 Android/iOS 系统能力，FFI 适合既有 C ABI 库等场景，但都需要序列化、线程和生命周期设计。

**追问：** FFI 能直接调用任意 Kotlin 对象吗？不能把 C ABI 与 JVM 对象互操作混成一回事，通常还要桥接。**易错：** “返回 Future”不代表接收端自动在后台执行。[平台通道](https://docs.flutter.dev/platform-integration/platform-channels) · [Dart FFI](https://dart.dev/interop/c-interop)

<a id="q41"></a>
### Q41 P0 SSH Mobile 的 Rust FFI 是否所有工作都在后台 Isolate

**回答：** 不是。已核对的 `NetworkNativeIsolate.sendCommand` 在调用者 isolate 同步经过 FFI；阻塞事件 poll 放在 helper isolate。Rust 内部使用 Tokio 也不会自动改变这次 C ABI 调用在 Dart 侧的执行位置。

**追问：** C 函数返回0能否显示任务成功？先区分提交入队、命令终态和真正业务 ready。**易错：** 不把类名中带 Isolate 当作线程模型证据。完整链路见 [SDK 源码导读](sdk-source-deep-dive.md)。

<a id="q42"></a>
### Q42 P0 跨 FFI 的内存和销毁顺序为什么危险

**回答：** Dart GC 不会自动理解 Rust handle 与原生分配内存的所有权。需要逐类规定谁分配、谁释放、是否复制、借用有效期，以及异步 poll 结束前是否还会读取 handle。停止读者与销毁对象的顺序必须由协议保证。

**追问：** mounted 为 false 后直接 free 指针行不行？页面状态与 native 使用者不是同一生命周期。**易错：** 不把 finalizer 当作所有资源及时释放和线程安全的替代方案。[C interop](https://dart.dev/interop/c-interop) · [项目内存表](sdk-source-deep-dive.md)

<a id="q43"></a>
### Q43 P0 冷启动按需初始化怎样避免第一次并发调用重复创建

**回答：** 把正在进行的初始化 Future 作为共享状态，多次调用等待同一任务；失败后按策略清理该 Future 允许重试；销毁与创建交错时避免发布已无主的资源。这常称为 single-flight，但不能仅缓存一个 Future 就忽略失败和生命周期。

**追问：** 把初始化延后是否一定改善用户体验？可能把成本转移到首次使用，应分别测首帧、可交互与首功能 ready。**项目联系：** NetworkRuntimeImpl 有对应按需创建与进行中任务复用逻辑；没有可复核的历史提速百分比。

## 七 性能 测试与工程实践

<a id="q44"></a>
### Q44 P0 Flutter 卡顿从哪里开始排查

**回答：** 固定真机、构建模式、数据和操作路径，先看 profile 下 DevTools 时间线，区分 UI 侧与 raster 侧耗时，再定位具体计算、布局、图片或原生任务。刷新率不同，单帧预算也不同；60Hz 约16.7ms，120Hz 约8.3ms。

**追问：** debug 模式很卡能否据此写优化结论？不适合作为用户体验性能基线。**易错：** 只数 build 次数或只看平均值，会漏掉少数严重慢帧。[Performance view](https://docs.flutter.dev/tools/devtools/performance)

<a id="q45"></a>
### Q45 P1 少 build 就一定更快吗 const 能完全阻止更新吗

**回答：** build 只是成本的一部分；局部状态、稳定配置和可复用 child 有机会减少无关工作，但还要看布局、绘制和资源开销。const 可帮助复用常量配置，不会冻结环境依赖，也不是全局禁用重建的开关。

**追问：** 为什么把输入区拆出来比每次整页 setState 更合理？让高频变化与真正依赖它的 UI 对齐。**易错：** 不为优化重写 Widget 的深层相等比较，引入更重的比较成本。[性能实践](https://docs.flutter.dev/perf/best-practices) · [ValueListenableBuilder](https://api.flutter.dev/flutter/widgets/ValueListenableBuilder-class.html)

<a id="q46"></a>
### Q46 P0 Dart 有 GC 为什么还会内存泄漏

**回答：** GC 只能回收不再可达的对象。未取消监听、Timer、静态集合或闭包可能持续引用页面；native 内存、图片与平台资源也有自己的管理路径。应在重复进入退出场景下观察对象存活、引用链与外部内存，而不是看到占用上涨就直接定性泄漏。

**追问：** 内存不立刻下降一定泄漏吗？可能是缓存或GC时机，需对照重复操作和回收后的趋势。**易错：** 不只看 Dart heap 就推断整个进程内存。[Memory view](https://docs.flutter.dev/tools/devtools/memory)

<a id="q47"></a>
### Q47 P1 图片缓存为什么可能导致 OOM

**回答：** 下载文件大小和解码后像素内存不同；大图、多张同时显示和 live 引用可能消耗大量内存。ImageCache 管理的是 Flutter 图片缓存，不等于通用磁盘 HTTP 缓存。可按显示需求控制解码尺寸，并审查预加载数量和释放时机。

**追问：** 把缓存上限调到很大是不是优化？可能减少重复解码，也可能加重内存压力。**易错：** 清理缓存不保证所有仍被引用的图片立刻释放。[ImageCache](https://api.flutter.dev/flutter/painting/ImageCache-class.html)

<a id="q48"></a>
### Q48 P0 单元测试 Widget 测试与集成测试分别证明什么

**回答：** 单元测试验证独立逻辑；Widget 测试验证受控环境中的组件行为；集成测试覆盖更完整的应用流程及平台交互。mock 通过不意味着真实网络、权限或 FFI ABI 正确，需要按边界补真实环境验证。

**追问：** pumpAndSettle 为什么有时超时？持续动画、计时器或不断调度帧可能没有稳定点，应有针对性地推进帧和断言。**易错：** 测试覆盖率不是业务正确率。[测试概览](https://docs.flutter.dev/testing/overview)

<a id="q49"></a>
### Q49 P0 hot reload hot restart 和重新安装有什么区别

**回答：** hot reload 尽量更新代码并保留当前 Dart 状态，不会重新执行所有初始化；hot restart 重启 Dart 应用状态；原生代码或某些构建配置变化通常需要完整重启或重建。它们对持久数据的影响也不同。

**追问：** 改了 initState 为什么效果没变？热重载不等于重新创建所有 State。**易错：** 不用 hot reload 后的状态证明真实冷启动路径正确。[Hot reload](https://docs.flutter.dev/tools/hot-reload)

<a id="q50"></a>
### Q50 P1 debug profile release 和 flavor 是一回事吗

**回答：** build mode 决定调试能力和优化方式；flavor 通常区分开发、测试、生产等应用配置，两者是不同维度。最终行为还取决于 Dart 入口、dart-define、Android 构建配置、依赖和签名等。移动端与 Web 编译方案也不能一概而论。

**追问：** release 连错环境怎么排查？先核对实际产物配置与入口，不只看 IDE 当前选项。**易错：** 客户端常量或混淆不是安全存储密钥的方法。[构建模式](https://docs.flutter.dev/testing/build-modes)

<a id="q51"></a>
### Q51 P0 Flutter 插件能否替代 Android 权限与生命周期知识

**回答：** 不能。插件只是包装平台能力，权限声明、运行时授权、Activity 结果、后台限制和资源持有仍受系统约束。要区分 FlutterEngine、Activity 与 Dart 页面生命周期，并处理授权拒绝、取消、Activity 重建及回调迟到。

**追问：** Dart 侧拿到文件 URI 能否永远访问？取决于平台授权与存储机制，不能当普通永久路径。**易错：** 不把插件 API 返回成功当成后续能力永远有效。此题是平台设计原则，具体限制须对照目标 Android 版本与插件实现。

<a id="q52"></a>
### Q52 P0 项目主要由 AI 辅助生成 面试如何证明 Flutter 能力

**回答：** 选一个能定位、解释、修改并验证的实际模块，说明状态归谁、异步结果如何关联、哪些资源谁释放、失败路径怎样处理。把 AI 生成、自己修改和自己验证分开讲；不把仓库中存在的复杂代码自动算成独立设计成果。

**追问：** 不用 AI 现在能改什么？应给具体功能和测试，而不是回答“都能”或“只会调 API”。**易错：** 新做的练习要标明日期，不能倒写成最初开发经历。配套使用 [代码接管练习册](ai-code-takeover-workbook.md)。

## 八 Flutter 与原生 Android 的对应关系

| Flutter 概念 | 可对比的 Android 问题 | 不能直接画等号的地方 |
| --- | --- | --- |
| Widget / Element / RenderObject | 界面描述、实例身份、布局绘制 | Widget 不是 Android View 对象，树结构不一一对应 |
| State 生命周期 | Fragment view 生命周期、页面资源清理 | dispose 不等于 Activity.onStop，页面隐藏也不等于销毁 |
| Dart UI isolate | 主线程响应与耗时任务隔离 | isolate 不是 Kotlin coroutine；async 不等于 Dispatchers.IO |
| Future / Stream | 一次结果与连续事件 | Stream 不自动等于有重放的 StateFlow，Future 不自带结构化取消 |
| Provider / Selector | 作用域注入、按需观察状态 | 不是 ViewModel 或 Hilt 的简单改名，职责要分别说明 |
| MethodChannel / FFI | 平台接口、JNI/native 边界 | 通道调用不自动后台执行；C ABI 也不是 Binder IPC |
| Navigator | 路由返回栈 | 不等于每个页面都对应一个 Activity，也不等于系统任务栈 |
| DevTools profile | 帧时间、内存与资源分析 | 仍需必要的 Android 平台诊断，Dart 指标不能覆盖全部原生资源 |

## 九 对照 SSH Mobile 的学习入口

以下例子按固定提交核对，回答时先解释代码，再说明自己是否读过、改过或验证过。源码链接不是公开访问授权。

### 例子一 聊天输入区怎样把高频更新局部化

`_ChatComposerState` 自己持有 `ValueNotifier<String>`，在 initState 监听传入的输入 Controller，在 dispose 移除监听并释放自己创建的 notifier；Controller 属于父级，不能顺手销毁。Selector 选取发送相关标志和附件等不可变快照，内部 ValueListenableBuilder 处理文本更新。异步 `_setPlanMode` 的 finally 分支检查 mounted 后再 setState。

**对应题目：** Q19、Q21、Q31、Q32、Q45。**面试追问：** 如果父级换了 Controller，旧监听是否解绑？如果操作结束时页面仍存在，但请求已过期，仅检查 mounted 是否够？这两点应沿具体代码验证，不能把示例概括成所有竞态均已解决。

[chat_composer.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/features/feature_ai/lib/src/chat/views/widgets/chat_composer.dart)

### 例子二 Runtime 怎样复用正在进行的初始化

`NetworkRuntimeImpl.ensureCapability` 按能力保存进行中的 Future，多次调用复用同一初始化；native handle 创建也有进行中任务复用。失败路径清理任务以允许后续重试。dispose 设置销毁状态、等待创建过程并关闭 handle，而不是只把字段赋 null。

**对应题目：** Q10、Q12、Q43。**面试追问：** 第一位调用者不再等待时，是否应该取消其他调用者共享的初始化？应区分请求拥有者与共享资源拥有者。本篇没有实际执行这些并发场景。

[network_runtime_impl.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/network_transport/lib/src/runtime/network_runtime_impl.dart)

### 例子三 FFI 命令和事件为什么是不同执行路径

`network_native_isolate.dart` 启动 helper isolate 处理原生事件轮询；命令 `sendCommand` 仍在调用者 isolate 进行同步 FFI。事件字节复制到 Dart 后释放对应 native buffer；命令临时分配则在 finally 清理。停止 worker 与销毁共享 handle 的顺序不能反过来。

轮询循环中让出执行机会，也关系到控制消息能否被及时处理。这是“事件循环调度”和“原生阻塞调用”如何交织的实际例子，不能只画一个后台线程框就结束。

**对应题目：** Q07、Q08、Q12、Q14、Q40—Q42。**面试追问：** `handle.address` 能跨 isolate 传递是否就证明内存安全？不证明，地址只是入口，真实所有权仍需协议维护。

[network_native_isolate.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart)

### 例子四 终端滚动状态与重绘边界

终端视图区创建 ScrollController 并注册监听，销毁时移除监听、释放自己持有的 Controller 与滚动指标 notifier。ValueListenableBuilder 把滚动指标变化用于相关区域；RepaintBoundary 与 TerminalView 自身的 key 分别承担绘制边界和组件身份的职责。

**对应题目：** Q17、Q19、Q28、Q31、Q45。**面试追问：** 一个字体设置变化应更新配置还是强行改变整个终端子树身份？先判断是否必须丢弃旧状态，再设计 key。当前代码没有动态 RepaintBoundary key，不代表所有场景的绘制性能都已测量。

[terminal_view_area.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/features/feature_terminal/lib/src/presentation/terminal_view_area.dart)

### 例子五 应用后台 flush 不等于可靠关机保存

`ConditionalAppLifecycleCoordinator` 注册并移除生命周期观察者，在 inactive、paused、detached 等分支触发异步 flush；detached 还涉及停止 MCP。若 flush 采用 unawaited 方式，它只是发起任务，不代表系统会等待任务持久化完成后才杀进程。

**对应题目：** Q10、Q34、Q36、Q46。**面试追问：** 哪些数据必须在平时及时落盘，而不能等到最后一刻？这是失败模型问题，不只是生命周期 API 记忆题。

[conditional_app_lifecycle_coordinator.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/services/conditional_app_lifecycle_coordinator.dart)

### 例子六 Android 凭据保护为什么用平台通道

`android_credential_crypto.dart` 使用 MethodChannel 调用 Android 凭据保护能力，包含能力探测及封装、打开、删除密钥等方法，并检查返回字节格式、映射 PlatformException。这里调用的是平台能力，不是 Rust 网络 FFI。

**对应题目：** Q02、Q39、Q40、Q51。**面试追问：** 能力探测成功后，用户取消、平台状态变化或实际操作失败，怎样向上层表达？不能将一次能力探测永久等同所有操作成功。本次没有确认 EventChannel 的具体使用，因此 EventChannel 在前文仅作为通用知识。

[android_credential_crypto.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/android_credential_crypto.dart)


## 十 六个可形成真实面试证据的练习

以下是建议开展的新练习，不是项目已通过的测试。全部先使用 fake 数据、测试替身或独立小示例，不要直接向真实服务器发送破坏性命令。

### 练习一 预测事件循环 再解释运行结果

写一个包含同步日志、scheduleMicrotask、Future 构造、Future.delayed 与 await 的小程序。先写预测顺序，再运行记录差异。再加入一个短时间递归微任务场景，观察普通 Timer 为什么被推迟。

**验收：** 能逐项说明来源与调度规则，不只记住一串输出。避免创建无终止递归造成运行环境卡死。本篇未代你运行该练习。

### 练习二 重排带输入框的列表

创建三个有独立输入状态的列表项，分别试无 key、下标 ValueKey、业务 ID ValueKey、每次新建 UniqueKey。输入内容后执行插入、删除和重排，记录状态跟随位置还是业务对象。

**验收：** 能解释 Element 复用和状态归属；证明正确性后再讨论性能，不能以截图“看起来正常”替代全部操作序列。

### 练习三 页面退出与旧请求回调

用两个 Completer 模拟请求 A、B，让 B 先返回、A 后返回，再增加页面退出。分别验证只检查 mounted、增加 request generation、支持底层取消三种设计。

**验收：** B 的结果不会被 A 覆盖；销毁后不更新 UI；能说明“忽略旧结果”与“取消远端副作用”的区别。对共享服务不能随页面关闭就无条件销毁。

### 练习四 把局部输入更新与整页更新做对照

建立消息列表与输入框，比较顶层 setState、局部 ValueNotifier/ValueListenableBuilder、Selector 选择不可变快照的方式。记录受影响的 build 范围，再在相同真机 profile 场景观察帧时间。

**验收：** 写明设备、模式、数据规模和操作，不只展示 build 次数减少。若帧时间没有明显改善，就如实记录；不要补造百分比。

### 练习五 有界文件管道与取消清理

用本地测试文件和可控慢消费者，比较整文件读取、分块但无限创建 Future、分块并等待消费三种方式。加入读到一半取消、写入失败和句柄关闭的检查。

**验收：** 说明峰值缓冲的来源、背压位置及清理责任，不把单块大小当整个进程内存上限。保持源文件与测试输出分离，避免覆盖原始材料。

### 练习六 初始化与 FFI 事件的安全替身

先不接真实 native 指针，写一个 fake Runtime：并发初始化两次只创建一次；失败后允许重试；初始化途中 dispose 不发布新资源。再模拟 commandId 对应的成功、超时、重复和迟到事件。

**验收：** 每个 pending 至多被完成一次，销毁后不继续向页面发布；能说明 fake 测试没有证明 C ABI 布局、原生线程安全或真实网络正确。完成后再在受控环境中补真正集成验证。

## 十一 面试前自检

- [ ] 我能解释一条从页面交互到状态更新的调用链。
- [ ] 我能区分 Dart 同步代码、异步 I/O、isolate 与原生工作线程。
- [ ] 我能说清 Controller、Subscription、Timer、native handle 的拥有者。
- [ ] 我能说明为什么某处要局部订阅、流式读取或按需初始化，也能说出代价。
- [ ] 我能说出至少一个未验证的边界，不把通用原理当现有实现保证。
- [ ] 我已经亲手完成至少两个练习，并保留失败输入、修改与结果。
- [ ] 我不会把 Flutter 经验替代 Android 原生知识，也不会把 AI 生成部分包装成独立手写底层协议。

推荐口述结构：**结论 → 项目中的具体位置 → 正常路径 → 失败或生命周期边界 → 验证方式。** 如果某处还没读懂，明确停在已掌握的范围，再说明会如何继续核对。
