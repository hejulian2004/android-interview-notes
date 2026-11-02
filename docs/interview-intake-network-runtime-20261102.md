# 用户面经补充：网络协议与跨端运行时

核对日期：2026-11-02。本文是依据用户提供的文字、截图题意编写的 **17 道深化练习**，不是公司官方题库，也不证明分享者实际参加过面试。原帖 URL 与可靠面试日期未提供；这些线索不并入仓库既有三年窗口的公开来源数量或公司频率统计。题意经过归纳，回答由整理者独立编写，不转载原帖全文，不把他人的项目经历写成用户经历。

本文补足既有题库的具体追问，保留原题路径及学习进度。协议按所引 RFC、Flutter 按平台及构建模式、RN 按架构代际区分；网页与 main 分支文档会变化，实际项目须核对锁定版本。这里没有运行抓包、端到端网络、真机或性能实验，不能据此声称某种框架更快或某项优化已取得收益。

已有入口：[网络基础 Q056—Q065](../questions/09-网络与网络库/README.md)、[跨端 Q092—Q095](../questions/14-Flutter与跨端/README.md)、[Flutter 52 题](flutter-interview-guide.md)。下文追问与答案是编辑性练习，不表示它们全部出现在原面试中。

## 绘制、线程与执行环境

<a id="nt01"></a>
### NT01 P0 Flutter、React Native 与 Android 的绘制到底在哪一层不同

**口述回答：** Android View 把状态和布局映射到原生视图树，经过测量、布局、绘制及系统合成显示；Compose 也是 Android 上的 UI 体系，不能简单等同 XML。Flutter 常规 Widget 由自己的框架和引擎布局绘制，不是为每个 Widget 创建一个 Android View；嵌入 Platform View 时另有集成成本。RN 将 React 的描述转换成宿主视图，新架构 Fabric 包含 C++ 渲染逻辑，不能只用“JS 通过旧 Bridge 发 JSON”概括当前实现。

**原理与边界：** 要分别比较组件模型、布局、绘制、宿主控件、线程和数据交换。Flutter 的 `Element.markNeedsBuild` 将元素标脏并经 BuildOwner 安排构建；它不表示每次销毁整棵 Element/RenderObject 树。Flutter 也依赖平台窗口、输入与图形能力；RN 也有布局、提交和挂载阶段。统一视觉、原生控件复用、复杂交互及现有模块迁移各有取舍。性能必须在同一业务、设备和 release/profile 条件下测量，开发模式的卡顿不能直接用于框架排名。

**追问 1：RN 新架构就完全没有跨语言开销了吗？答：** 没有这个保证。调用频率、对象转换、调度、布局及宿主操作仍有成本，只是不能全部归因于旧 Bridge。

**追问 2：Flutter 的 build 等于 Android 的 draw 吗？答：** 不等于。build 更新配置并协调 Element；布局、绘制和合成是后续不同阶段，参考 [Flutter Q27](flutter-interview-guide.md#q27)。

**易错点：** “Flutter 完全不依赖原生”“RN 都使用 WebView”“跨端只测一端”都不成立。这里深化 [Q095](../questions/14-Flutter与跨端/Q095-ReactNative-与原生或其他跨端方案怎样比较.md)，没有重建同义基础题。

**官方参考：** [Flutter 架构](https://docs.flutter.dev/resources/architectural-overview)、[Element.markNeedsBuild](https://api.flutter.dev/flutter/widgets/Element/markNeedsBuild.html)、[BuildOwner](https://api.flutter.dev/flutter/widgets/BuildOwner-class.html)、[RN Fabric](https://reactnative.dev/architecture/fabric-renderer)、[RN Render/Commit/Mount](https://reactnative.dev/architecture/render-pipeline)。

<a id="nt02"></a>
### NT02 P0 Java 共享内存、Dart Isolate 和 RN 的线程模型怎样比较

**口述回答：** Java 线程通常共享进程堆，需要明确可见性、原子性与复合操作同步。Dart 应用代码在 Isolate 内通过事件循环执行，Isolate 之间主要使用消息通信，普通可变对象不当作共享对象随意并发读写。RN 要区分 JS 执行、宿主 UI 和 native 工作；新架构的渲染阶段还可能按优先级在不同线程运行，不能把 JS 线程和系统 UI 线程视为同一条。

**原理与边界：** 单个 Isolate 的回调不会像两个 Java 线程那样同时执行 Dart 指令，但 `await` 会让其他事件插入。两个“先读余额、等待、再写余额”的异步任务仍可发生逻辑竞态。FFI/native 库又有自己的线程、共享资源与锁，不能用 Dart 隔离内存替它们证明线程安全。

**追问 1：Flutter 单线程是否不需要考虑同步？答：** 仍须维护请求顺序、版本号、取消和结果失效等不变量；涉及 native 共享资源时还需其自身同步协议。

**追问 2：把计算写成 async 就用了多核吗？答：** 不会自动发生。CPU 工作须评估 Isolate、平台线程或 native 任务；通信和复制成本也要计入，已有 [Flutter Q07/Q12](flutter-interview-guide.md#q07) 讲具体边界。

**易错点：** 不要说整个 Flutter 引擎只有一条线程，也不要说 RN 所有渲染永远只发生在 JS 线程。

**官方参考：** [Dart 并发](https://dart.dev/language/concurrency)、[RN Threading Model](https://reactnative.dev/architecture/threading-model)、[JLS 内存模型](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html)。

<a id="nt03"></a>
### NT03 P0 TypeScript 有自己的线程模型和虚拟机吗，宏任务微任务怎样解释

**口述回答：** TypeScript 通常检查并转换成 JavaScript 后由相应 JS 引擎执行，类型声明不会自动变成运行时验证，所以不能给 TS 单独指定一个通用线程模型。浏览器环境中，脚本、定时器等按任务调度；Promise reaction、`queueMicrotask` 等在微任务检查点执行。一个检查点会继续处理新加入的微任务，因此无限补充微任务也能饿死后续任务与渲染。

**原理与边界：** 引擎与宿主不同：V8/Hermes 是引擎，浏览器提供 DOM 和相关事件循环集成，Node 与 RN 也各有宿主。浏览器里常说的“宏任务”对应讨论中的 task，但不是“全球唯一先进先出队列”；多个任务源与渲染机会都有规则。Worker 可以提供独立执行环境，不能据主事件循环推导整个应用只有一个线程。

**追问 1：`setTimeout(f, 0)` 会立刻执行吗？答：** 不会，它排入后续调度，还受当前任务、微任务、宿主计时和节流约束。

**追问 2：JS 有虚拟机还算解释语言吗？答：** 语言与实现策略不能一一对应。引擎可能解释字节码并分层编译；Hermes 还可预编译字节码，不等于所有 JS 都以同一方式 JIT。

**易错点：** `as User` 和 TS 接口不会替接口响应做运行时校验；不能把浏览器、Node 的任务顺序原样套到所有 RN 版本。

**官方参考：** [TypeScript Erased Types](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)、[HTML 事件循环](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)、[V8 引擎](https://v8.dev/docs)、[RN Hermes](https://reactnative.dev/docs/hermes)。

<a id="nt04"></a>
### NT04 P1 面试官问 C 或 Java 的堆栈谁快，应该先澄清什么

**口述回答：** 先澄清是在比较对象分配、访问、回收还是函数调用。常见 native 实现的自动存储可通过调整栈指针管理，通用动态分配器要管理空闲块；这只能说明机制差异，不能推导每次访问堆都比栈慢。缓存局部性、优化、逃逸、分配器和数据规模会改变实际成本。原题的“调用堆和调用栈”也可能是表述混淆，不能直接背固定倍数。

**原理与边界：** C 语言标准定义存储期，而不是规定所有变量必须落在哪种硬件栈。Java 的抽象机有每线程栈、帧和共享堆；实际运行时可内联方法、优化分配，不能把语义存储区直接当最终机器布局。Java 代码在 Android ART、桌面 HotSpot 的实现也不能混为一谈。

**追问 1：局部引用在栈里，就代表对象在栈里吗？答：** 不是。引用变量和所引用对象不同；再讨论实现优化时，还要有目标运行时证据。

**追问 2：C 肯定比 Java 函数调用快吗？答：** 不成立。是否内联、间接调用、ABI、边界检查和优化状态都影响结果，要用代表性负载测量。

**易错点：** “堆每次访问都要查表”“GC 语言的分配必定更慢”都是过度推导。本题是对含糊面经的澄清与对照练习，不声称原帖要求了某种具体 ABI。

**官方参考：** [JVMS 2：运行时数据区与实现自由](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html)、[ART 执行与 JIT](https://source.android.com/docs/core/runtime/jit-compiler)。[WG14 C11 草案 N1570 §6.2.4](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf) 为标准委员会原始入口，本次网页工具访问超时，C 存储期细节应再对照目标编译器文档核读；没有据此生成编译器性能数字。

<a id="nt05"></a>
### NT05 P0 JIT、AOT、解释执行与 Flutter 动态化为什么不能按语言贴标签

**口述回答：** 解释执行在运行时按解释器规则执行程序表示；JIT 在运行中编译部分代码；AOT 在目标运行前编译。它们是实现策略，可以混合。Dart Native 开发与发布模式的编译方式不同，Web 又可生成 JS 或 Wasm；ART 也会结合解释、JIT、profile 和 AOT。因此“Java 只能 JIT”“JS 没虚拟机”“Flutter 永远不能动态更新”都不准确。

**原理与边界：** 移动端常规 Flutter release 中 Dart 业务通常为 AOT 机器码，不能把开发热重载当成线上任意下发 Dart 源码的机制。配置驱动 UI、服务端数据、嵌入 Web 内容、改变已编译原生代码是不同能力；专门热更新方案还涉及平台限制、兼容、安全和发布策略。能热更新不代表可以绕开平台审核规则。

**追问 1：AOT 是否不用 runtime 和 GC？答：** 不一定。Dart AOT 仍需要类型、内存和 Isolate 管理；编译成机器码不等于获得 C 的内存模型。

**追问 2：怎么验证项目用哪种模式？答：** 检查目标平台、构建命令、产物和运行配置；性能测量用适合的 profile/release 模式，不能只看语言文件后缀。

**易错点：** 不把热重载、热重启、线上热更新当同一件事；不能给一种语言永久绑定一种执行模式。

**官方参考：** [Dart 平台与编译器](https://dart.dev/overview#platform)、[Flutter 构建模式](https://docs.flutter.dev/testing/build-modes)、[Flutter 热重载](https://docs.flutter.dev/tools/hot-reload)、[ART JIT](https://source.android.com/docs/core/runtime/jit-compiler)。

<a id="nt06"></a>
### NT06 P0 Android 为什么有 DEX，和 class 文件、寄存器、ART 是什么关系

**口述回答：** DEX 是 Android 运行时使用的字节码和文件组织格式，不是把 class 改扩展名。它的指令模型使用虚拟寄存器，集中索引字符串、类型、字段和方法等信息，适合组织多个类。传统 JVM class 的指令执行模型以操作数栈为基础；这些都是抽象机模型，DEX 寄存器并非直接等于 CPU 寄存器。

**原理与边界：** Java/Kotlin 编译产生的 class 可经 D8 等工具转换为 DEX，启用 R8 时还涉及缩减和优化；之后由目标系统 ART 执行与编译。DEX 的组织和常量索引能减少重复表达，但不能承诺所有 APK 更小、所有指令更快。某些格式索引限制会引出 multidex；不能将不同 DEX 版本的容量特性混写。

**追问 1：为什么不用 class？答：** Android 选择了配套的运行时、工具链和移动端文件组织。回答可比较文件及指令结构，不能声称 class 在硬件上“绝对不能执行”。

**追问 2：Dalvik 和 ART 是两种 DEX 吗？答：** 它们是不同代运行时，均围绕 DEX；ART 并不是把所有 Java 直接改成 native 源代码。

**易错点：** Java 字节码、DEX、ELF 共享库和最终 CPU 指令属于不同层；不要把打包、安装编译、运行优化合成一步。

**官方参考：** [AOSP DEX 文件格式](https://source.android.com/docs/core/runtime/dex-format)、[Dalvik 字节码](https://source.android.com/docs/core/runtime/dalvik-bytecode)、[ART 与 Dalvik](https://source.android.com/docs/core/runtime)、[JVMS 指令与帧](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html)。

## TLS、TCP 与 HTTP 的追问

<a id="nt07"></a>
### NT07 P0 请按一次 TLS 1.3 完整握手解释 HTTPS，而不是背 RSA 交换密码

**口述回答：** 以常见证书认证、非 PSK 恢复的 TLS 1.3 为例，客户端 ClientHello 提供参数及 key share；服务端选择参数、返回自己的 key share，双方据密钥协商结果派生握手密钥。服务端发证书、CertificateVerify 和 Finished；客户端校验证书链、域名、签名与握手完整性，再发 Finished，之后用应用流量密钥保护数据。证书用于认证，密钥协商不等于把固定会话密码用证书公钥发过去。

**原理与边界：** 算法、消息和 RTT 必须带版本前提；TLS 1.2 的旧 RSA 密钥交换不能当成 TLS 1.3 通用流程。会话恢复、客户端证书、HelloRetryRequest 会改变细节。HTTP/3 的安全握手集成在 QUIC 中，也不是普通“先 TCP，再 TLS”的连接图。

**追问 1：HTTPS 能证明服务端业务没有恶意吗？答：** 不能，它解决传输中的认证、保密与完整性，服务端如何使用数据仍是另一层问题。

**追问 2：TLS 0-RTT 请求能无条件执行扣款吗？答：** 不能；早期数据有重放风险，业务须限制允许的操作并设计幂等或拒绝该请求。

**易错点：** 不跳过域名或证书校验来“解决”代理失败；不能把哈希、签名、密钥协商、对称加密当成同一算法。基础入口保留 [Q058](../questions/09-网络与网络库/Q058-HTTPS-如何建立可信且加密的连接.md)。

**官方参考：** [RFC 8446 §2/§4 TLS 1.3 握手与 §8 0-RTT](https://www.rfc-editor.org/rfc/rfc8446.html)、[RFC 9001 QUIC 使用 TLS](https://www.rfc-editor.org/rfc/rfc9001.html)。

<a id="nt08"></a>
### NT08 P0 三次握手最后一个 ACK 有什么用，第一次 SYN 丢了怎样重试

**口述回答：** 常规主动建连是 SYN(x)、SYN(y)+ACK(x+1)、ACK(y+1)，同步两个方向的初始序号。第三步让服务端得到对自身 SYN 的确认，也有助于防止旧重复建连报文造成错误连接，不能只背“证明能收能发”。第一次 SYN 未获回应时，TCP 按重传定时机制再次发送；等待多久、重试多少次还受操作系统、socket 选项和应用连接超时约束。

**原理与边界：** 不能从“客户端没收到回复”断言 SYN 一定丢了，也可能是 SYN-ACK 丢失。RTO 有退避规则；Linux 的 `tcp_syn_retries`、部分内核的线性超时设置等会改变实际时序，因此不把网上的“固定 1、3、7 秒，必重试某次数”当跨平台常量。应用超时返回也须检查底层连接是否已取消。

**追问 1：第三个 ACK 丢了，客户端是否必定立即断开？答：** 不一定。服务端可能重传 SYN-ACK，后续满足规则的报文也参与状态处理；应按状态机分析，而非另造一次全新业务连接。

**追问 2：为什么两次不够？答：** 服务端发送 SYN-ACK 后尚未得到客户端对自己序号的确认，旧 SYN 场景也可能造成错误状态；第三步完成正常同步。基础关闭流程见 [Q057](../questions/09-网络与网络库/Q057-TCP-建连与关闭连接为什么需要握手.md)。

**易错点：** 不用浏览器请求超时值代表内核 SYN 重试策略，不承诺所有建连恰好三包、没有重传。

**官方参考：** [RFC 9293 §3.5 建连](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.5)、[RFC 6298 重传计时器](https://www.rfc-editor.org/rfc/rfc6298.html)、[Linux IP sysctl](https://docs.kernel.org/networking/ip-sysctl.html)。

<a id="nt09"></a>
### NT09 P0 服务端怎样知道 TCP 客户端断开，心跳是否能保证实时准确

**口述回答：** 正常关闭、异常复位和静默失联不同。收到 FIN 表示对端不再发送数据，读到 EOF 并不代表自己不能继续发送；收到 RST 或 I/O 错误可发现部分异常。断网、掉电或中间设备丢状态可能没有报文到达，空闲连接不会凭空立刻知道失联，需要写入与超时、TCP keepalive 或业务心跳等机制。

**原理与边界：** 这里区分 TCP 连接状态与业务会话状态。心跳间隔、超时阈值、网络抖动、移动端休眠和服务器负载会造成延迟与误判；重连后需会话版本、幂等和恢复协议，不能仅靠心跳承诺零丢失。TCP ACK 说明传输层接收进展，不证明对方业务已落盘或执行。

**追问 1：`write()` 成功是不是对方在线？答：** 可能仅把数据交给本地缓冲；不证明对端应用已读，也不保证稍后不报错。

**追问 2：心跳设得越频繁越好？答：** 会增加唤醒、电量、流量和服务压力；应按业务容忍时间设计，并验证弱网与休眠条件。

**易错点：** keepalive、HTTP 持久连接和业务心跳不是一回事；“未收到 FIN 就在线”不成立。

**官方参考：** [RFC 9293 §3.6 关闭、§3.8.4 Keep-alives](https://www.rfc-editor.org/rfc/rfc9293.html)、[Linux TCP keepalive 参数](https://docs.kernel.org/networking/ip-sysctl.html)。

<a id="nt10"></a>
### NT10 P0 TCP 流量控制和拥塞控制为什么要分开，四阶段适用于所有算法吗

**口述回答：** 流量控制避免压垮接收端，关注对方通告的接收窗口；拥塞控制避免向网络注入过多数据，维护拥塞窗口等状态，二者会共同约束发送。经典 Reno 风格可从慢启动、拥塞避免、快速重传、快速恢复解释：探测容量、收到 ACK 后增长，出现丢失时调整。它是学习入口，不是所有现代实现的逐步行为。

**原理与边界：** `rwnd` 与 `cwnd` 都是窗口概念，但信号来源不同。不能把接收窗口为零当成链路拥塞，也不能说 UDP 应用没有拥塞控制义务。实际系统可能使用 CUBIC 或其他算法；比较算法必须核对内核配置、网络、RTT、丢包、排队和吞吐，不能背“每次丢包窗口必定减半”作为唯一答案。

**追问 1：丢包一定是拥塞吗？答：** 不一定，例如无线错误也可能丢包；但具体算法要依据可用信号决策，不能由应用随意关闭拥塞控制。

**追问 2：窗口大就一定快吗？答：** 还受链路容量、RTT、接收能力、拥塞与应用读取速度影响，过度排队还可能增大延迟。

**易错点：** 慢启动的“慢”不是每个 RTT 都线性增长；拥塞避免和可靠重传有关联但不等同。

**官方参考：** [RFC 5681 经典 TCP 拥塞控制](https://www.rfc-editor.org/rfc/rfc5681.html)、[RFC 9438 CUBIC](https://www.rfc-editor.org/rfc/rfc9438.html)。

<a id="nt11"></a>
### NT11 P0 HTTP 1.0、1.1、2 的头部和多路复用差在哪，HPACK 是加密吗

**口述回答：** 先区分 HTTP 方法与状态等语义，和在线路上传输的表示。HTTP/1.x 使用文本起始行和字段表达；1.1 完善持久连接等机制。HTTP/2 用二进制帧承载多个流，字段块经 HPACK 编码，并用 `:method`、`:path`、`:scheme`、`:authority` 等伪头表达请求控制信息。HPACK 是压缩，不提供保密，TLS 才是相关传输安全机制。

**原理与边界：** HPACK 使用静态表、动态表及字符串编码减少重复；其压缩状态需要按协议维护。HTTP/2 多路复用减少 HTTP/1.1 队列中的某些阻塞，但共享 TCP 丢包仍可影响多个流，不能说它没有队头阻塞。HTTP/2 不让业务方法突然获得新的幂等含义，也不是所有头字段都可以原样搬过去。

**追问 1：HTTP/2 可以抓文本看到 `GET / HTTP/2.0` 吗？答：** 这不是其网络请求行表示；调试工具可能为了展示生成类似文本，实际要按帧和伪头解释。

**追问 2：用了 HTTP/2 就一定比 1.1 快吗？答：** 不一定，要看请求并发、连接复用、流量大小、丢包、服务与代理支持等。

**易错点：** 不把 HPACK 当 gzip 响应体压缩，也不将 HTTP/3 的 QPACK 当 HTTP/2 的实现。

**官方参考：** [RFC 1945 HTTP/1.0](https://www.rfc-editor.org/rfc/rfc1945.html)、[RFC 9112 HTTP/1.1 消息语法](https://www.rfc-editor.org/rfc/rfc9112.html)、[RFC 9113 HTTP/2](https://www.rfc-editor.org/rfc/rfc9113.html)、[RFC 7541 HPACK](https://www.rfc-editor.org/rfc/rfc7541.html)。

<a id="nt12"></a>
### NT12 P0 GET、POST、PUT 怎么选择，请求超时后可以自动重试吗

**口述回答：** GET 用来获取目标资源的表示，POST 请求目标按自身语义处理内容，PUT 请求以所给表示创建或替换指定目标状态。要回答语义、安全性和幂等性，而不是只说“参数在 URL 还是 body”。PUT 和安全方法在语义上幂等；POST 不因此天然幂等，但业务可用幂等键、唯一约束和结果查询设计可安全重试的接口。

**原理与边界：** 幂等指重复同样请求的预期效果，不要求每次响应状态码、日志完全相同。超时只表示客户端没有按时得到结果，服务端可能已经提交；自动重试会放大风险。方法也不替代服务端实现契约，错误地用 GET 修改状态仍会出问题。

**追问 1：POST 比 GET 安全吗？答：** 不天然；HTTPS、日志脱敏、认证授权和服务端校验才是不同层的保证。URL 容易进入历史与日志，也不代表 body 从不被记录。

**追问 2：PUT 的重试是否能忽略并发更新？答：** 不能；还要考虑版本、条件请求等并发控制，否则幂等写也可能覆盖别人的新状态。

**易错点：** 不编整个 HTTP 协议统一 URL 字节上限；GET 内容没有普遍定义的语义，不应靠它传递必须被所有中间件理解的请求体。基础题 [Q059](../questions/09-网络与网络库/Q059-GET-和-POST-的差别是否只是参数位置.md) 保留。

**官方参考：** [RFC 9110 §9 方法、§13 条件请求](https://www.rfc-editor.org/rfc/rfc9110.html)。

<a id="nt13"></a>
### NT13 P1 URL 到页面流程中 CDN 处在哪，缓存 key 为什么会影响正确性

**口述回答：** URL 解析后先考虑浏览器、应用和已有连接的缓存，未命中再经历域名解析、选路、连接与安全握手、请求响应、解析与展示。CDN 把内容分发到边缘节点，可能命中缓存，也可能回源；它不是一律把 DNS 解析到“物理最近”的服务器。节点策略、网络质量、负载和内容命中都会影响结果。

**原理与边界：** 缓存 key 必须区分影响表示的维度，如目标资源、必要查询参数及 Vary 对应请求头；登录身份和权限相关内容不可随意进入共享缓存。版本化资源可减少更新歧义，但不该删除真正影响结果的参数来提高命中率。DNS 缓存、HTTP 缓存、图片解码缓存是不同层。浏览器拿到 HTML 后还涉及 DOM/CSSOM、脚本及子资源、渲染树、布局与绘制；阻塞脚本可能影响解析，响应首字节不等于页面可交互。

**追问 1：`no-cache` 是不准保存吗？答：** 主要要求复用前验证；`no-store` 才是相应禁止存储指令，仍需理解其适用范围。

**追问 2：CDN 缓存了私有接口怎么办？答：** 先阻止错误共享、清理相关缓存并核查暴露范围，再修正响应指令、key 与鉴权边界；这是通用事故处理框架，不是个人经历。

**易错点：** CDN 命中不等于 HTTPS 被绕过，CDN 也不自动替代授权。URL 基础流程复习 [Q060](../questions/09-网络与网络库/Q060-从输入-URL-到收到响应会经历哪些步骤.md)。

**官方参考：** [RFC 9111 HTTP 缓存](https://www.rfc-editor.org/rfc/rfc9111.html)、[AWS CloudFront 工作原理](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/HowCloudFrontWorks.html)、[Google 浏览器渲染树与布局](https://web.dev/articles/critical-rendering-path/render-tree-construction)。CloudFront 是具体厂商实现，不能当成所有 CDN 的统一算法。

## 混合开发与需要澄清的题意

<a id="nt14"></a>
### NT14 P1 RN 页面为什么可能迁到 H5，JSBridge 新接口如何兼容老版本

**口述回答：** 迁移原因应依据真实业务，如发布节奏、现有 Web 能力复用、宿主接入成本和性能需求，不能从“RN 支持热更新”推断它永远优于 H5。Bridge 接口要定义方法与版本、参数、返回、错误、超时、取消及能力查询；页面先探测宿主是否支持，再决定走新接口、降级或提示升级，而不是只按 App 版本号猜能力。

**原理与边界：** JSBridge 暴露的是 native 权限边界。只加载受信内容、限制导航目标、验证消息来源与参数，按能力最小暴露；WebView 的 `addJavascriptInterface` 会暴露给 frame，不能假设校验顶层 URL 就认证了所有调用者。异步结果还应带请求 ID，页面退出后停止交付旧结果。

**追问 1：给接口加个 v2 就完成兼容了吗？答：** 还要约定旧参数缺省值、未知字段、错误码和降级行为，测试新 H5/旧客户端与旧 H5/新客户端组合。

**追问 2：RN 能热更新为什么还改 H5？答：** 热更新只是一个维度，依赖原生能力的变更仍可能要求发版；实际原因只能由项目上下文证明。

**易错点：** 不给未提供源码的截图项目编造迁移收益；也不开放任意反射、任意 URL、任意命令的桥接入口。

**官方参考：** [Android WebView native bridge 安全边界](https://developer.android.com/privacy-and-security/risks/insecure-webview-native-bridges)、[WebView addJavascriptInterface](https://developer.android.com/reference/android/webkit/WebView#addJavascriptInterface(java.lang.Object,%20java.lang.String))、[RN 架构](https://reactnative.dev/architecture/overview)。本次已读取风险指南，WebView API 页直读超时；接口可用性仍须按目标 API 核查。

<a id="nt15"></a>
### NT15 P1 Dart GC 是不是三代三算法，AOT 后由谁管理对象

**口述回答：** 不应把帖子作者随口给出的代数和算法数当事实。Dart Native VM 的官方实现文档描述分代 GC，新生代与老生代采用不同回收策略；并行、并发、暂停等是不同维度。AOT 只是编译模式，并没有取消 Dart runtime 的内存管理。Dart Web 则要结合 JS 或 WasmGC 目标，不能把 native VM 堆实现原样套过去。

**原理与边界：** 所引 VM 文档描述两个代：新生代使用并行暂停式 semispace scavenger，老生代有并发标记配合清扫或压缩策略。这是当前所读实现文档的描述，不是 Dart 语言承诺的永久算法。GC 能回收不再可达的托管对象，不会自动撤销 Stream 订阅、释放一切 native 资源，也不能收回仍被全局对象持有的页面。

**追问 1：分配频繁但堆没有一直涨，是没性能问题吗？答：** 仍可能频繁回收、暂停并争夺 CPU；需用 profile 数据关联分配和帧时间，不能只看峰值。

**追问 2：有 GC 就不用 dispose 吗？答：** 不成立。生命周期清理是释放外部资源和订阅；具体可参考 [Flutter Q46](flutter-interview-guide.md#q46)。

**易错点：** 不照搬 HotSpot 的分代与收集器名称，也不说 AOT 二进制没有 GC。

**官方参考：** [Dart VM GC 实现说明](https://github.com/dart-lang/sdk/blob/main/runtime/docs/gc.md)、[Dart runtime 与平台](https://dart.dev/overview#runtime)。main 可变，面试涉及算法细节须核对项目 Dart SDK 版本。

<a id="nt16"></a>
### NT16 P1 Flutter 路由和网络请求应怎样分开，混合页面返回栈怎么设计

**口述回答：** 原截图把“网络请求、原生插件、某开源路由”放在一起，库名和具体问题不完整，应先区分导航路由与网络请求路由。Flutter Navigator 管理 Route 栈，Router 把外部导航信息映射到页面状态；Android Activity 任务栈和 iOS 导航容器又有各自生命周期。混合项目要约定谁拥有栈、返回键由谁消费、结果如何回传与恢复，不能把一个 Flutter Route 固定等同一个 Activity。

**原理与边界：** Flutter Web 还需同步 URL、浏览器前进后退和深链；移动端还需权限、宿主销毁及系统返回手势处理。网络客户端是否走 Dart、平台通道或 native SDK，要从调用链验证，不能看路由库名推断。截图提到但未完整标识的框架保留待澄清，不擅自补成某个库的实现。

**追问 1：App 被回收再点深链，直接 push 页面够吗？答：** 还要构造有效导航状态、校验参数和登录权限，并处理已有页面/冷启动两条入口。

**追问 2：混合多引擎能共用同一个 Dart 单例吗？答：** 不能默认。要先核对引擎与 Isolate 的实例边界，再设计共享状态和消息协议。

**易错点：** 路由是页面组织能力，不自动提供网络传输、权限校验或跨平台相同返回行为。

**官方参考：** [Flutter Navigator/Router](https://docs.flutter.dev/ui/navigation)、[Flutter 深链](https://docs.flutter.dev/ui/navigation/deep-linking)、[Flutter add-to-app](https://docs.flutter.dev/add-to-app)。

<a id="nt17"></a>
### NT17 P0 TCP、UDP、IP 与 OSI 七层怎么对应，为什么不能说 UDP 一定快

**口述回答：** TCP 和 UDP 属于传输层，IP 负责网络层的分组寻址与转发。TCP 提供有序可靠字节流及流量、拥塞控制，但不保留业务消息边界；UDP 提供数据报边界，协议本身不负责 TCP 那套连接与可靠交付。OSI 七层从低到高是物理、数据链路、网络、传输、会话、表示、应用；实际 TCP/IP 协议栈不必机械拆成七个独立实现。

**原理与边界：** 数据报应用仍要处理大小、丢失、乱序、安全和拥塞，不能把 UDP 当作没有约束的高速通道。QUIC 就在 UDP 之上实现可靠流、安全与恢复机制，已有 [Q061](../questions/09-网络与网络库/Q061-QUIC-基于-UDP-为什么仍能提供可靠流.md) 深入说明。因此比较应给出业务需求、延迟、损失容忍、网络条件与实现，不能仅凭协议名宣布速度。

**追问 1：TCP 可靠为什么接口还超时？答：** 连接仍会失效，且传输成功不等于业务处理完成；应用还需要超时、幂等和业务确认。

**追问 2：TLS 一定是独立的 OSI 表示层吗？答：** 七层是参考模型，具体协议组合不必严格一对一；应直接画实际 HTTP/TLS/TCP/IP 或 HTTP/3/QUIC/UDP/IP 栈。

**易错点：** UDP 不保证无丢失、低延迟或安全，TCP 不保证一次业务请求只执行一次。

**官方参考：** [RFC 9293 TCP](https://www.rfc-editor.org/rfc/rfc9293.html)、[RFC 768 UDP](https://www.rfc-editor.org/rfc/rfc768.html)、[RFC 8085 UDP 使用指南](https://www.rfc-editor.org/rfc/rfc8085.html)、[ITU-T X.200 OSI 参考模型入口](https://www.itu.int/rec/T-REC-X.200)。

## 重复题与练习导航

const/final/late 直接复习 [Flutter Q01](flutter-interview-guide.md#q01)；三棵树与生命周期复习原指南 Q15—Q23，标脏与 BuildOwner 的补充见 NT01；原生通信复习 Q40/Q51；普通异步和 Isolate 复习 Q07—Q13。这里保留既有题号，而不把每张重复截图复制成新题。

原帖的“Wind Object”按上下文作为 RenderObject 的可能笔误处理，不能声称存在一种独立 Flutter 类型。面试日期、项目网络库和具体路由框架无法仅凭截图确认，仍需原帖链接或源码。以上比较都是通用练习，不替代 SSH Mobile 的固定版本源码导读。
