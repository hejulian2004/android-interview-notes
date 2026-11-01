# 源码导读：Rust SDK、C ABI 与 Flutter 异步边界

> 核对版本：`hejulian2004/ssh_mobile` 的 `main`，提交 `5aba1d83405d53bdabd3807c76139489d17d7e6a`，2026-11-01 阅读。文中源码链接固定到此提交。源仓库为私有仓库，链接需要访问权限。本文公开的是解释与学习路线，不复制整个私有实现。
>
> “源码已实现”表示本次阅读确实看到了对应逻辑；“设计解释”是对代码的推导；“练习”是建议补做，并不代表作者已经完成或测试已经通过。本次是静态源码核对，没有运行手机、Rust 网络集成测试或性能基准。项目大量使用 AI 辅助生成代码，下面的实现不能自动算作个人独立设计成果。

## 1. 先分清：项目里并不只有一个叫 SDK 的东西

你可以把整个系统想成“业务接口、资源管理、跨语言桥、原生执行引擎”四层，不能把所有代码都叫 QUIC。

| 层 | 项目位置 | 主要职责 | 不应混淆的边界 |
|---|---|---|---|
| 面向功能的客户端契约 | `packages/infrastructure/network_sdk` | 对 Feature 暴露类型化业务会话、结果、事件 | 不直接拥有 Socket、FFI handle 或底层协议状态 |
| 应用级 Runtime / Transport | `packages/infrastructure/network_transport` | 按需创建能力、管理 native handle，向适配器借出 gateway | gateway 是借用接口，不是另造一个原生 Runtime |
| Dart 原生绑定 | `packages/infrastructure/ssh_mobile_network_native` | 将 Dart 类型/字节映射到 C ABI，持有 runtime handle、轮询 isolate | 不等于 Android MethodChannel；这是 `dart:ffi` 路径 |
| Rust SDK | `native/network_core/crates/*` | 生命周期、命令分发、连接/传输/安全等领域实现 | 依赖成熟库，不等于从零写 QUIC、TLS 或加密算法 |

Rust workspace 中又区分 `network-core`、`network-protocol`、`network-identity`、`network-nat`、`network-quic`、`network-transfer`、`network-relay`、`network-relay-proto`、`network-transport`、`network-webrtc`、`network-ffi`。crate 是 Rust 的编译/依赖组织单元，不是操作系统进程。目录分得多，也不自动证明每一层边界都正确。

**“自研”的合理边界：** 项目内开发了业务契约、资源生命周期、命令/事件桥接、连接与传输状态协调；协议和基础算法主要调用依赖库。更稳妥的简历表达是“基于 Rust 与成熟传输库构建项目内网络 SDK”，个人职责再单独说明。

源码入口：[native/network_core/Cargo.toml](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/Cargo.toml#L1-L16)；[packages/infrastructure/network_transport/lib/src/runtime/network_runtime_impl.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/network_transport/lib/src/runtime/network_runtime_impl.dart#L18-L40)；[packages/infrastructure/network_transport/lib/src/native/native_network_adapter.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/network_transport/lib/src/native/native_network_adapter.dart#L62-L104)。

## 2. 为什么选择 C ABI，而不是直接把 Rust 对象交给 Dart？

### 2.1 ABI 是调用约定，不是网络协议

API 回答“提供哪些功能”；ABI 回答“二进制层面函数怎样被找到、参数如何传递、结构体怎样布局”。Rust 的普通 `String`、`Vec`、trait object 不能直接当成稳定的跨语言契约。

当前实现有三个重要约束：

- 用 `extern "C"` 导出函数，并使用 `#[no_mangle]` 保留可查找的符号名。
- 运行时只暴露不透明的 `*mut c_void` handle。Dart 知道这个地址，但不解释 Rust 内部结构。
- 事件缓冲区使用 `#[repr(C)]` 的 `SshNetBuffer { ptr, len }`，Dart 必须用匹配的指针和 `Size` 布局读取。

`network-ffi` 的 crate 类型包含 `cdylib` 与 `rlib`。前者适合给非 Rust 使用者链接，后者保留 Rust 库用途。**这不代表每个平台实际产物和加载方式完全相同**，构建流水线仍需另查。

当前 `SSH_NET_ABI_VERSION` 是 1，而 Network Protocol 是 V2。两个版本不冲突：函数形状可不变，而编码消息的协议版本独立演进。

源码：[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L24-L43)；[native/network_core/crates/network-ffi/Cargo.toml](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/Cargo.toml#L1-L14)；[packages/infrastructure/ssh_mobile_network_native/lib/ssh_mobile_network_native.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/ssh_mobile_network_native.dart#L26-L54)。

### 2.2 不透明指针不是安全凭证

handle 本质上仍是地址。`is_null()` 只能排除空指针，不能判断一个非空地址是否有效、是否已释放、是否来自另一个 runtime。

`catch_unwind` 的作用是尝试把 Rust panic 转成错误返回；它**不能**修复非法指针、重复释放、数据竞争等未定义行为，也不能保证捕获 abort 模式的进程终止。FFI 安全需要调用方遵守约定，不能只靠 Rust 语言自身的内存安全承诺。

面试追问：为什么 Rust 项目还会出现 use-after-free？

参考要点：安全 Rust 的检查只覆盖其语言规则内的行为；跨 FFI 的裸指针和 `unsafe` 需要人工维护所有权与生命周期。Dart GC 不知道 Rust 对象何时还能被后台 poll 使用。

## 3. 内存所有权：三类内存，三个释放规则

| 对象 | 谁分配 | 谁使用 | 谁释放 | 关键条件 |
|---|---|---|---|---|
| 命令字节临时区 | Dart 通过 `calloc` 分配 | 同步 FFI 调用内借给 Rust 解码 | Dart 的 `finally` | Rust 不应在函数返回后继续借用该裸指针 |
| 事件字节区 | Rust 编码后转 boxed slice | Dart 复制为自己的 `Uint8List` | `ssh_net_buffer_free` | 必须先复制，再由 Rust 对应释放入口回收 |
| Runtime 对象 | Rust `Box::new` 后 `Box::into_raw` | Dart 持有不透明句柄；poller 与 Rust 使用 | Rust destroy 内 `Box::from_raw` | 先停止使用者、再停 worker、最后释放 |

### 3.1 命令方向的实际实现

`NetworkNativeIsolate.sendCommand` 名字容易误导：这个方法在调用它的 Dart isolate 上同步执行，**并没有通过 SendPort 把命令发送工作交给轮询 isolate**。

它分配临时字节区、复制命令、调用 C ABI，最后 `calloc.free`。Rust 的 `ssh_net_runtime_command` 在调用期间将指针转借用 slice，用 `prost::Message::decode` 得到拥有其字段的 `NetworkCommand`，再把命令交给运行时队列。因此当前桥接不是“零拷贝”。

源码：[packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart#L118-L133)；[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L491-L547)。

### 3.2 事件方向为什么要复制两次字段？

Rust 编码事件，交出 `ptr + len`；Dart 先保存 `bufferPtr` 和 `bufferLen`，再复制字节并释放 Rust 缓冲区。

`outBuffer.ref` 是原生结构体的一层视图，不是独立值拷贝。如果先把原结构体的 ptr 清空，再从所谓的旧 `ref` 读取，就可能已经丢掉实际地址，导致无法复制或释放。

当前代码用 `Uint8List.fromList(bufferPtr.asTypedList(bufferLen))` 取得独立 Dart 字节副本。它随后清空临时结构体，再调用专门的 Rust free。结构体容器本身和它指向的事件字节是两块不同内存，不能只释放其中一个。

源码：[packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart#L193-L242)；[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L551-L642)。

### 3.3 应该能回答的三个反例

1. **事件直接拿 `asTypedList` 返回，马上 free，会怎样？** 那是原生内存视图；释放后的读取不安全，当前实现因此先复制。
2. **Rust 内存用 Dart `calloc.free` 回收行不行？** 不应假设分配器和布局兼容，应走配对的 Rust 释放函数。
3. **反复调用 destroy 是否天然安全？** 不安全。裸指针第二次可能已经悬空；Dart 用生命周期与置空保证自己的正常调用路径不重复释放，并不让任意外部调用都变安全。

## 4. 线程、Isolate、Tokio：不要把三者讲成同一件事

当前有三种执行边界：

1. **Dart UI isolate**：业务状态、页面逻辑及正常命令提交。普通同步 FFI 调用仍占用调用者，返回 Future 也不会自动把内部同步工作移走。
2. **Dart helper isolate**：运行阻塞式原生事件轮询，并通过 `SendPort` 返回已经复制的字节。
3. **Rust Tokio 多线程 Runtime**：调度原生异步任务、网络 I/O 和命令 worker。多任务不等于每个任务各占一个 OS 线程。

`NetworkRuntime::new` 构建 `new_multi_thread().enable_all()` Runtime；`start` 才启动命令 worker。`new` 并不是零成本：它已经创建 Tokio runtime。只有再往应用级延迟 create，才能把这部分初始化移出初始启动路径。

Rust 的 `poll_event` 在非零超时情况下使用 runtime handle 的 `block_on(timeout(...))`，因此需要离开 UI isolate。Dart 默认轮询等待值为 50ms，表示一次 poll 最多等待多久，**不是“所有事件固定延迟50ms”或“UI只刷新20次/秒”**。有事件可提前返回，代码还通过零时延 Future 把执行机会交还给 helper isolate 的消息循环。

源码：[native/network_core/crates/network-core/src/runtime/facade.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/runtime/facade.rs#L19-L77)；[native/network_core/crates/network-core/src/runtime/facade.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/runtime/facade.rs#L337-L352)；[packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart#L68-L114)。

### 4.1 Rust 同步原语怎样理解？

- `Arc<T>`：共享所有权的引用计数。它不会自动使所有内部读写线程安全。
- `Mutex<T>`：互斥访问。短时间保护命令发送器或事件接收器；不要把“用了锁”理解成无竞争问题。
- `AtomicU8`：表示运行时生命周期，通过 compare-exchange 控制状态转换。
- Tokio `mpsc`：多生产者、单消费者的异步通道，命令入队和真正执行分离。
- `Notify`：唤醒等待者，不应当作保存所有历史消息的队列。

这些解释对应当前 runtime 的组合使用，但不能推导“整个 SDK 无锁”或“完全无竞争”。

## 5. 一条真实调用链：发起 Realtime 会话

> 选择这一条，是因为它从 App 适配器一直贯穿到底层命令/事件系统，方便练习完整闭环。**Realtime 与 QUIC 可靠传输不是同一个协议通道**；本节演示共享 SDK 桥接，不能据此说屏幕媒体全部走 QUIC。UI 点击所在 Feature 入口不在本节审查范围。

### 5.1 去程：从业务命令到 Rust worker

1. `AppRealtimeSessionBackend.start(realtimeId, peerId)` 进入 `_sendCommand`。先检查对象可用性与 pending 容量，等待 `_ensureGateway` 后再检查一次，避免等待期间状态变化。
2. `NetworkRuntimeImpl.openRealtimeGateway` 先保证 realtime capability，就同一个 native handle 返回 `RuntimeNetworkRealtimeGateway`；它不是新建第二套底层连接引擎。
3. `RuntimeNetworkRealtimeGateway.start` 生成 commandId，调用 `NativeNetworkProtocol.startRealtimeSessionCommand`。编码器校验字段，将 realtimeId、peerId、可选 screenVideo 放进 Protobuf 消息。
4. `_send` 先登记命令跟踪，再通过 `_RuntimeCommandGateway → NativeNetworkHandle → NativeNetworkRuntime.sendCommand → NetworkNativeIsolate.sendCommand` 提交字节。
5. Rust `ssh_net_runtime_command` 检查空指针、长度、命令ID，解码 Protobuf、登记 pending，然后调用 `NetworkRuntime.send_command`。
6. `send_command` 检查 Runtime Running 状态，用 `try_send` 放入有界 mailbox。这里返回0只是**同步边界接收/入队成功**。
7. Rust `run_command_worker` 取出消息，经 ledger 和协议版本校验后分派 `StartRealtimeSession` 到 `crate::realtime::start_session`，再发出命令结果事件。

源码：[apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart#L189-L201)；[packages/infrastructure/network_transport/lib/src/realtime/network_realtime_gateway.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/network_transport/lib/src/realtime/network_realtime_gateway.dart#L128-L172)；[packages/infrastructure/ssh_mobile_network_native/lib/src/native_protocol_command_encoder.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/native_protocol_command_encoder.dart#L269-L300)；[packages/infrastructure/network_transport/lib/src/runtime/network_runtime_impl.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/network_transport/lib/src/runtime/network_runtime_impl.dart#L102-L125)；[packages/infrastructure/network_transport/lib/src/runtime/network_runtime_impl.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/network_transport/lib/src/runtime/network_runtime_impl.dart#L227-L240)；[packages/infrastructure/network_transport/lib/src/native/native_network_adapter.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/network_transport/lib/src/native/native_network_adapter.dart#L88-L118)；[packages/infrastructure/ssh_mobile_network_native/lib/ssh_mobile_network_native.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/ssh_mobile_network_native.dart#L172-L179)；[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L491-L547)；[native/network_core/crates/network-core/src/runtime/facade.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/runtime/facade.rs#L315-L334)；[native/network_core/crates/network-core/src/commands/ledger.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/commands/ledger.rs#L77-L131)；[native/network_core/crates/network-core/src/commands/ledger.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/commands/ledger.rs#L187-L209)；[native/network_core/crates/network-core/src/commands/ledger.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/commands/ledger.rs#L284-L300)。

### 5.2 回程：为什么 commandId 很重要？

1. Rust 命令处理产生 `NetworkEvent`，C ABI poll 取出事件并编码成字节。
2. helper isolate 复制事件、释放 native buffer，通过 SendPort 发回 Dart。
3. gateway 解码并经过 command result guard，App backend 的 `_onNativeEvent` 消费类型化事件。
4. `_completeCommand` 用 commandId 找到原来的 Completer，移除 pending、取消 timer，并完成 `SdkSuccess` 或 `SdkFailure`。V2 结果还会校验 pending 中的 peerId 与事件的 peerId 一致。
5. 会话状态和快照事件另行更新生命周期。**命令结果完成、会话已就绪、第一帧已显示，是不同层次的事实。** 是否能发送媒体仍需看真实会话状态，不能只看 queue success。

源码：[apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart#L238-L286)；[apps/ssh_mobile_full/lib/app/realtime_feature_adapters_events.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/realtime_feature_adapters_events.dart#L141-L168)；[apps/ssh_mobile_full/lib/app/realtime_feature_adapters_events.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/realtime_feature_adapters_events.dart#L184-L210)；[packages/infrastructure/network_transport/lib/src/realtime/network_realtime_gateway.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/network_transport/lib/src/realtime/network_realtime_gateway.dart#L138-L149)。

### 5.3 超时、取消与迟到结果

当前 App backend 默认 pending 上限32、等待结果30秒。timer 到时移除对应 pending 并返回 timeout；dispose 则清空 pending、取消timer并完成 cancelled。迟到结果因为查不到 pending 而不再完成原 Future。

但**调用方超时不等于远端操作已停止**。这段 timeout 处理本身没有展示向底层发送取消命令。需要真正取消副作用时，还要检查具体业务取消接口、服务端状态与幂等策略。

同样，页面/适配器 dispose 释放的是自己订阅和待完成请求，不能随意关闭 App Scope 借来的共享 Runtime。只有真正的资源 owner 应执行底层销毁。

源码：[apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart#L238-L286)；[apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart#L288-L298)；[apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart#L328-L373)。

## 6. “有界、去重、成功”这三个词最容易讲过头

### 6.1 多层容量不是一个“最大并发数”

| 位置 | 当前源码值 | 正确解释 |
|---|---:|---|
| App Realtime pending | 默认32 | 本适配器等待结果的容量，不是所有网络业务并发上限 |
| FFI pending command | 64 | FFI 边界未终结命令ID预算 |
| Core command mailbox | 256 | 待 worker 消费的控制命令队列容量 |
| FFI terminal history | 1024 | 有界已完成ID历史，旧ID会淘汰 |
| Core completed ledger | 4096 | 另一层有限已完成ID集合，重启也不保留 |

这些是不同责任层的配置，不要把它们直接相加、乘起来当吞吐指标。命令 worker 当前逐条等待 `dispatch_command`；部分领域可自行派生后台任务。单看 Tokio 多线程不能保证所有命令处理并行。

源码：[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L24-L34)；[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L185-L222)；[native/network_core/crates/network-core/src/commands/ledger.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/commands/ledger.rs#L24-L73)；[native/network_core/crates/network-core/src/runtime/mod.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/runtime/mod.rs#L43-L53)；[apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/apps/ssh_mobile_full/lib/app/realtime_feature_adapters.dart#L238-L286)。

### 6.2 事件有界不等于不丢事件

FFI 的 `EventMux` 把事件分成 critical control、normal control、data：

- 控制事件共享条目和字节预算，达到上限时 enqueue 会失败。
- data lane 超预算时会淘汰最旧项，再放入新项。
- 若 data 有积压，连续控制事件达到8个后轮到data，防止单侧长期饥饿。
- 每次从Core最多 drain 512个，避免一次无限读取。

因此可说“设置了容量上限与公平调度”，**不能说“所有事件无损可靠交付”**。当前 `drain_runtime_events` 对 mux.enqueue 的布尔返回值没有向上报告；测试时要特别观察消费者长期停顿时命令结果与业务数据的最终处理。这里只指出代码可见边界，不声称已经复现线上丢事件故障。

注意：`SshStreamDataReceived` 等也被归入data，不应把整个data lane笼统解释为“丢掉无关紧要的进度通知”。业务能否接受丢弃，必须回到相应流和消费链核验。

源码：[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L108-L181)；[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L331-L370)。

### 6.3 “exactly-once”必须说清范围

有限ID集合只能在保留窗口内识别历史ID；它不是持久化事务日志。进程重启、ID淘汰、超时重试与远端副作用，都使“所有操作全局恰好执行一次”成为额外问题。

更准确的表达是“按commandId关联结果、限制本地重复完成并清理超时请求”。业务级不重复写文件、不重复执行远程命令，要靠对应业务幂等/确认协议，不能由 Completer 一次完成直接推出。

## 7. 安全停止：先停读者，再释放被读对象

`NativeNetworkRuntime.dispose` 的主线：

1. 生命周期进入stopping，阻止新的正常命令进入。
2. `await _poller.stop()`：先通知helper isolate退出并等待exit确认。
3. 然后调用 native stop，清理原生worker与相关资源。
4. stop成功后调用 native destroy，最终把Dart handle设为nullptr并进入destroyed。

helper isolate 先等待正常退出；超时可kill，但仍等待退出确认。**kill请求发出不等于已经停止访问指针。** 如果强制退出也没有得到确认，代码抛错并保留相关状态，避免继续destroy造成悬空访问。代价可能是暂时保留资源，需要后续恢复或诊断；不能因此承诺所有失败都绝不泄漏。

Rust destroy 内也调用内部stop，并让原生媒体owner注册失效后再释放Box。这个防护不代替Dart先确认poller停止的职责。

源码：[packages/infrastructure/ssh_mobile_network_native/lib/ssh_mobile_network_native.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/ssh_mobile_network_native.dart#L333-L415)；[packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/network_native_isolate.dart#L155-L189)；[native/network_core/crates/network-ffi/src/lib.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-ffi/src/lib.rs#L650-L675)。

### 面试口述版本

“Runtime 是共享原生资源，Dart 的轮询 isolate 也会访问同一个句柄。所以销毁顺序必须先阻止新请求、确认 poller 已退出，再停 Rust worker，最后释放 handle。仅把 Dart 指针设为 null 不会阻止另一个 isolate 用已经复制过去的地址访问对象。”

这是对源码的解释，不代表你亲自设计了这套机制；介绍个人工作时应补充真实承担的部分。

## 8. 错误模型与协议演进

### 8.1 有三层错误，不是一个异常

- **FFI即时返回**：参数不合法、解码失败、Runtime停止、队列提交失败等，发生在消息入队阶段。
- **命令结果**：消息已经进入worker，但业务校验或实际处理失败，通过相关联事件返回。
- **长期业务状态**：命令成功后，会话、传输仍可断线/失败，需要监听状态与终态事件。

当前通用 `NativeOperationStatus.fromNativeCode` 把 `-1/-2` 映射invalidArgument、`-4`映射stopped，其他非0映射failure。FFI内部更细的重复ID、容量等负码不会全部原样暴露给业务。媒体ABI另有专门转换，不能把两套错误码混用。

### 8.2 Protobuf 为什么也会出兼容问题？

Protobuf 解决字段编码，不自动解决业务含义兼容。Dart 当前有项目内 `_ProtoWriter` 与对应decoder，Rust用prost；两边字段号、枚举值、oneof、尺寸预算都必须一致。

例如当前start realtime的payload在外层命令使用字段21，内部字段1/2承载realtimeId/peerId，字段3是可选screenVideo。修改字段号不是简单重命名。新增值要考虑老decoder、未知事件处理和错误边界。

FFI最大事件为1MiB，而Dart协议文件还设置了更小的事件上限384KiB及各类payload预算。**边界的最小允许值和具体消息类型共同约束可传递的数据**，不是只看最外层1MiB就宣称所有消息都支持1MiB。

练习：画出一条新增命令所需同步修改的位置，至少包括协议定义、Rust分发、Dart编码/解码、公开类型、调用方及兼容测试。不要在学习时随意复用已有字段号。

源码：[packages/infrastructure/ssh_mobile_network_native/lib/src/native_operation_status.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/native_operation_status.dart#L22-L49)；[packages/infrastructure/ssh_mobile_network_native/lib/src/native_protocol_command_encoder.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/native_protocol_command_encoder.dart#L269-L300)；[packages/infrastructure/ssh_mobile_network_native/lib/src/native_realtime_protocol.dart](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/packages/infrastructure/ssh_mobile_network_native/lib/src/native_realtime_protocol.dart#L23-L43)。

## 9. 面试追问与实操验收

### Q1：为什么不直接让Flutter持有Quinn connection？

答题要点：避免Feature依赖Rust库的具体资源与生命周期；原生层维持单一owner，Dart只见契约和事件。代价是序列化、跨边界复制与异步状态协调更复杂。它是工程取舍，不是“Rust一定比Dart快”的结论。

### Q2：Rust有async，为什么还需要Dart isolate？

Rust内部异步不改变C ABI调用在Dart调用者上同步执行的事实。这里poll最终会block_on等待事件，所以移到helper isolate。命令发送本身仍是同步FFI，不能说所有native工作都已自动离开UI线程。

### Q3：收到0返回值，能否显示“连接成功”？

不能。0先表示同步提交成功，之后还要等command result；最终ready/connected状态又是另一层。UI必须与真正的业务状态绑定。

### Q4：如何证明没有重复完成Future？

用fake gateway输入同ID重复结果、先timeout后结果、先dispose后结果，观察调用方只完成一次、timer被取消或结束、pending回到基线。源码阅读和测试断言共同提供证据，不能只说“Dart是单线程所以没问题”。

### Q5：把Buffer大小调大就能提高吞吐吗？

不能直接推断。更大缓冲可能减少短期拒绝，也可能增加内存、尾延迟和GC/复制成本。应固定负载、观察生产与消费速率，再决定增加预算、合并可丢事件或对不可丢事件施加背压。

### 练习A：手动画一条命令的“谁拥有谁”图

选择本节Realtime start。标出commandId、临时命令指针、Rust解码对象、queue、事件缓冲、Dart副本、Completer。

**验收：** 不看文档说出每个对象何时创建、谁释放、失败时谁清理；能解释没有跨调用借用命令临时指针。

### 练习B：写安全的fake命令结果测试

不要人为向真实FFI塞悬空地址。用fake gateway模拟：提交失败、匹配结果成功、错误peerId、重复结果、超时后迟到、dispose后迟到。

**验收：** 提交失败不遗留pending；匹配结果唯一完成；错误目标不误完成；dispose清理本对象订阅，不关闭共享Runtime。

### 练习C：把“有界”变成能观察的行为

用独立纯Dart/Rust小模型模拟快生产者、慢消费者，记录队列长度、拒绝/淘汰数量与最大等待时间。再对照FFI mux策略，区分可合并进度与不可随意丢失的业务字节。

**验收：** 能说明何处是背压、何处是拒绝、何处是丢弃，以及为什么“内存有界”不代表“业务正确”。这是练习建议，不能写成项目已通过压力测试。

### 练习D：检查“停止失败”分支

仅通过测试替身让poller stop不确认退出、native stop失败或destroy失败，观察状态与重试行为，不触碰真实失效指针。

**验收：** 未确认poller退出时不destroy；失败不伪装成功；正常重复dispose共享完成过程；知道保守保留资源与立即释放的安全取舍。

## 10. 这一章学完后，应能讲清的最小闭环

不必背全部函数名，但必须能够回答：

- 当前项目的业务SDK、transport facade、native绑定和Rust核心分别是什么。
- 哪些能力是项目封装，哪些来自依赖库。
- 一条命令如何跨语言进入队列，结果如何找到对应调用者。
- 谁拥有三类内存，为什么不能提前释放。
- queue accepted、command finished、business ready为什么不同。
- 超时为什么不自动取消副作用，有限去重为什么不是全局exactly-once。
- 你自己目前能独立改动并验证哪一段，哪些仍需要AI辅助或继续学习。
