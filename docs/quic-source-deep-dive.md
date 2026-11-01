# QUIC、路径选择与可靠文件传输：对照源码理解网络 SDK

> 核对版本：`hejulian2004/ssh_mobile` 的 `main`，提交 `5aba1d83405d53bdabd3807c76139489d17d7e6a`，核对日期 2026-11-01。本文说明的是这一版本实际代码，不代表作者已经独立掌握全部实现，也不代表做过安全审计或真机性能测试。源码仓库为私有仓库，以下固定版本链接需要有权限的 GitHub 账号登录。
>
> 阅读目标：能区分“现成协议库做了什么”“项目封装做了什么”“我本人能解释和修改什么”。不要把本文当成个人经历背诵。

## 1. “自研 QUIC SDK”到底自研了什么？

更准确的表述是：**项目内实现了一套 Rust 网络 SDK，在成熟 QUIC、TLS 和密码库之上，封装设备身份、路径建立、消息与文件协议、断点恢复、跨语言接口及生命周期管理。**

这里“SDK”是向上层提供接口的一组组件，不是一种新的网络协议，也不等于从零写 QUIC。

| 层次 | 当前实现 | 应该怎样解释 |
| --- | --- | --- |
| QUIC 协议栈 | `quinn = "0.11"` | 使用成熟实现，不声称自行实现丢包恢复、拥塞控制或 QUIC 握手 |
| TLS | `rustls = "0.23"`、`rcgen` | TLS 实现和临时证书生成依赖库 |
| 异步运行时 | `tokio` | 网络、文件和任务调度依赖 Tokio；项目组织业务任务与状态 |
| 设备身份 | `network-identity`、`ed25519-dalek` | 项目定义可信设备及校验流程，签名算法由库实现 |
| 应用握手 | `snow`，Noise XX | 项目封装身份绑定、会话绑定、安全策略和密钥交换流程 |
| 应用加密 | `aes-gcm`、`hkdf` | 项目管理方向、密钥代际、nonce、AAD；不自创加密算法 |
| 业务传输 | `network-core`、`network-transfer` | 项目定义 offer、审批、offset、SHA-256 校验、完成确认、暂停和恢复 |
| Flutter 接口 | `network-ffi` 等 | 把上述能力暴露给 Dart，详见 SDK/FFI 专章 |

依赖声明中的版本是 Cargo 约束，**不是本文核实过的 Cargo.lock 最终解析版本**。

源码：[network-quic/Cargo.toml](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-quic/Cargo.toml)、[network-core/Cargo.toml](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/Cargo.toml)。

## 2. 先建立正确的分层图

```text
Flutter 业务功能
    ↓ SDK 命令与事件
network-ffi / network-protocol
    ↓
network-core：业务编排、会话、路径、认证、状态恢复
    ├─ network-nat：候选地址与发现相关能力
    ├─ network-quic：QUIC endpoint、设备握手、应用通道帧、文件流协议
    ├─ network-relay：控制面、reservation 与 Relay 数据面
    ├─ network-transport：其他通用传输适配
    └─ network-transfer：文件 manifest、流式读写、业务状态机
```

这不是逐行调用图，而是职责图。真实路径会因业务能力、安全策略和已有连接而不同。

三个概念一定要分开：

- **Topology（拓扑）**：Direct 还是 Relay，即数据是否经过中继。
- **Transport（传输）**：QUIC、TCP、UDP、WebSocket 等，即用什么承载。
- **Capability（能力）**：可靠消息、可靠字节流、不可靠数据报，即业务需要什么。

`ConnectionProfile` 将三者组合。不要把“Relay”当成和“QUIC”同一层级的协议名称，也不要看到 WebSocket 就认定只能直连或只能中继。

更重要的是：**抽象层宣称具备 ReliableStream，不意味着每个上层业务都实现了全部传输适配。**当前 `TransferDispatcher::select_attempt` 明确接受 QUIC，或 Relay 拓扑下的 WebSocket；其他组合返回“selected path cannot carry file transfer”。因此不能因为通用 TCP profile 支持字节流，就声称当前文件业务已完整支持 TCP 直传。

源码：[connection/profile.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/connection/profile.rs)、[transfer.rs：TransferDispatcher](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/transfer.rs)。

## 3. QUIC endpoint 怎样建立？

入口是 `QuicEndpointManager::from_bound_socket`：

1. 接受一个已经绑定的 UDP socket，并设置非阻塞。
2. 生成临时自签名证书，构造 rustls server/client 配置。
3. 将 ALPN 设置为 `ssh-mobile/2`，表示双方协商的是本项目应用协议。
4. 构建 Quinn endpoint，并设置默认客户端配置。
5. 配置 10 秒 keep-alive；这只是保活配置，不代表“断网 10 秒必定发现”或“耗电已优化”。

为什么接受已有 socket？代码明确说明，它可以先用于 STUN 和候选地址发现，再交给 QUIC，以保留外部观察到的源端口。**发现了公网映射不等于一定打洞成功**，还受 NAT、防火墙、映射有效期和对端状态影响。

`Endpoint` 可以理解为本机 QUIC 通信入口；`Connection` 是与某一对端建立的连接；`Stream` 是连接中独立的字节流。不要把三者混成一个“socket”。

源码：[endpoint.rs：QuicEndpointManager](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-quic/src/endpoint.rs)。

## 4. 连接选择不是一句“直连失败就走 Relay”

当前主入口是 `ConnectivityAttemptCoordinator::connect_with_capabilities`，带整体时间预算，执行大致如下：

1. 检查 runtime 配置、设备身份、对端配置与路由授权。
2. **Stage A：纯直连。**优先复用满足能力的现有 direct path；否则使用仍有效的候选缓存或配置地址，在限定时间内尝试直接连接。这个阶段不依赖 Relay 控制面在线。
3. 直连不成功时，还会检查是否已有满足能力的健康路径可以复用，避免无意义地产生新的协调票据。
4. **Stage B：经控制面协调。**通过权威 Resolve 和 Offer 事务获取对端状态及协调机会，继续进行连接尝试。`NotReady` 只允许一次受总预算限制的等待重试，不能把本地缓存伪装成服务器返回 Ready。
5. **Relay fallback：有条件回退。**需满足路由授权、协调状态及剩余预算等要求，申请 reservation，建立 Relay 数据连接，完成应用认证及加密握手，再发布可供业务使用的路径。

两条面试重点：

- 控制面用于查找、协调和申请中继资源；数据面传输业务内容。**控制面断开与已有数据路径失效不是同一个事件。**
- “路径可用”还要匹配业务能力。文件需要可靠流，不能随便拿一个能发消息的通道当文件通道。

并发候选连接还有一个容易忽略的问题：多个候选可能先后成功。`admit_single_winner` 在接纳之前复查当前 Session/路径状态，拒绝迟到的 loser，避免它把刚接好的 winner 替换掉。这里的难点是并发状态归属，不是“调用 connect 即可”。

源码：[entry.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/connect/connectivity_attempt/entry.rs)、[stage_a.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/connect/connectivity_attempt/stage_a.rs)、[stage_b.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/connect/connectivity_attempt/stage_b.rs)、[coordinated.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/connect/connectivity_attempt/coordinated.rs)、[relay_stage.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/connect/connectivity_attempt/relay_stage.rs)、[direct_quic.rs：admit_single_winner](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/peer/direct_quic.rs)。

## 5. 安全为什么分好几层？

### 5.1 临时 TLS 证书不等于可信设备身份

`ApplicationIdentityVerifier::verify_server_cert` 不执行普通公网 CA 信任链认证，而是接受临时自签名证书；TLS 签名验证仍委托给 rustls。

这不是“反正加密了就安全”。项目依赖随后的设备身份认证：`QuicPeerSession::perform_handshake` / `accept_trusted` 使用预期或已固定的 Ed25519 公钥检查对端，签名载荷绑定设备身份、nonce、角色 domain 和 TLS exporter 导出的当前连接材料。

**TLS exporter binding 的意义：**如果攻击者分别与两端建立不同 TLS 连接，不能简单转发某次正确的应用签名，就把两条连接伪装成原来的同一条连接，因为签名绑定的 exporter 值不同。

必须承认的信任前提：最初的可信公钥如何配置和分发仍然重要；握手不能自动解决“最初就保存了错误公钥”的问题。

源码：[endpoint.rs：ApplicationIdentityVerifier](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-quic/src/endpoint.rs)、[peer_session.rs：perform_handshake / accept_trusted / export_channel_binding](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-quic/src/peer_session.rs)。

### 5.2 为什么设备握手后还有 Noise？

`connect_direct_with_crypto` 先完成上述 QUIC 设备认证，再调用 `initiate_quic_with_policy`。第二阶段处理应用 Session 绑定、安全策略协商和应用密钥材料。

当前 Noise pattern 是 `Noise_XX_25519_AESGCM_SHA256`，由 `snow` 实现。每次握手生成新的 X25519 密钥材料，长期 Ed25519 设备身份用于身份签名，而不是直接充当每个业务数据包的加密密钥。

`PathHandshakeV2` 并不是又一套独立密码协议，它是现有握手内承载的认证元数据和 admission 演进。

安全策略不能随意降级：

- Direct 双方都选择 Disabled 时，允许 `IdentityOnly`。
- 双方都选择 Required 时，进入 `E2ee`。
- 双方策略不一致返回错误。
- Relay 任何一方选择 Disabled 都被拒绝，因为中继场景要求应用层 E2EE。

**IdentityOnly 不等于直连文件明文上网。**QUIC 本身仍有 TLS 保护；该名称说的是额外应用加密层的策略。

源码：[crypto_handshake/mod.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/crypto_handshake/mod.rs)、[noise.rs：NoiseHandshake::new](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/crypto_handshake/noise.rs)、[quic.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/crypto_handshake/quic.rs)、[path_handshake.rs：negotiate_security](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/path_handshake.rs)。

### 5.3 AES-GCM 的 nonce 和 AAD 是干什么的？

应用加密上下文根据发送方向、密钥代际 epoch 和计数器组织 nonce，并按消息数/字节数阈值轮换代际。关键原则是**同一密钥不能重复使用 nonce**，不能只背“用了 AES 所以安全”。

AAD 是参与认证但不一定加密的关联信息，用来防止密文被错误移到其他业务上下文。Relay 文件分块调用 `file_chunk_aad`，关联 crypto session、transfer、manifest hash 与 sequence。

重要边界：**当前直连文件路径直接把分块写入 QUIC stream，未经过 Relay 那套每块 AES-GCM 应用信封；它依赖 QUIC/TLS 的传输保护。**Relay 文件则显式调用 `encrypt_application_payload`。不要把一条路径看到的加密封装泛化成所有业务路径。

源码：[crypto/context.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/crypto/context.rs)、[relay_transfer/files.rs：send_file_over_relay](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/relay_transfer/files.rs)、[transfer_operations/send.rs：send_file](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/transfer_operations/send.rs)。

## 6. 同一 QUIC 连接中的 stream 怎样分工？

- **应用消息通道：**`send_channel_frame` 为一帧打开单向 stream，写入 magic `SMCH`、版本、类型、长度和 payload，再 finish。类型包含 DataMessage、DeliveryAck、RealtimeSignal。
- **文件传输：**使用独立双向 stream，一边发 offer 和文件数据，反方向返回审批、恢复 offset 和完成确认。
- **认证握手：**使用专门的双向 stream；不要把所有双向 stream 都理解为文件流。

`read_channel_frame` 在分配 payload 前检查长度，当前上限是 48 KiB。这是协议帧上限，**不是文件大小上限**。独立流和不同 magic 帮助协议分流，避免把业务消息误解析成文件头。

为什么还要写长度？QUIC stream 仍然是字节流接口；应用需要知道一帧有多长，不能假设一次 read 对应一次 write。

多流不意味着完全互不影响：它们仍共享连接级拥塞与资源。不要用“多流”推导出大文件不会影响实时消息的绝对保证。

源码：[channel.rs：send_channel_frame / read_channel_frame](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-quic/src/channel.rs)、[file_stream.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-quic/src/file_stream.rs)。

## 7. 一次直连文件发送：沿真实函数阅读

这条链只讲 Rust 内部，Flutter 到命令入口见 SDK/FFI 专章。

```text
accept_file_send
  → prepare_outgoing_file：廉价校验
  → 后台 start_file_send
      → build_file_manifest：文件信息与完整 SHA-256
      → TransferDispatcher::select_attempt：选择支持文件业务的 PathLease
      → TransferManager::register_outgoing：登记业务状态
      → dispatch_outgoing
          → send_file
              → 再检查源 manifest
              → connection.open_bi
              → write_file_offer
              ← read_file_decision：接受与接收端 offset
              → stream_send_file_cancellable：seek + 分块发送
              → finish
              ← read_file_completion：等待接收端完成确认
              → mark_completed / TransferCompleted 事件
```

### 7.1 接受命令不等于发送完成

`accept_file_send` 在廉价校验后启动后台任务并返回。哈希和选路失败通过 `TransferFailed` 事件报告，而不是把“已接受”当成最终成功。UI 应根据事件展示真实状态。

### 7.2 Manifest 为什么不仅有文件名？

它包括 transfer ID、文件名、文件大小、修改时间、内容哈希和协议版本。发送尝试会重新构建 manifest 与原值比较，防止恢复时不小心把“旧文件前半段”和“新文件后半段”拼起来。

这仍不能推导出对任意并发写文件都有完美快照隔离。当前路径不是先创建不可变快照再发送；若要保证发送期间源文件不会变化，需要额外策略与测试。最终接收哈希校验是另一道检测，不是源文件锁。

### 7.3 文件传输协议怎样表达请求和确认？

`write_file_offer` 写入 `SMFT`、文件协议版本、受限长度的 transfer ID/文件名、大小、修改时间、32 字节 SHA-256。接收端返回“接受标志 + u64 offset”。完成确认是独立的 `FILE_COMPLETION_ACK` 标记。

文件协议版本和网络协议版本是两个常量，不能只凭名字相似认为必须同值。

源码：[send.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/transfer_operations/send.rs)、[sender.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-transfer/src/sender.rs)、[manifest.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-transfer/src/manifest.rs)、[file_stream.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-quic/src/file_stream.rs)。

## 8. 接收端为什么比“read 然后存文件”复杂？

`handle_incoming_file_after_offer` 的主要顺序：

1. 校验并登记传输，向上层发 IncomingOffer。
2. 等待用户审批；超时默认不接受。
3. 检查是否已有完整且哈希一致的目标文件；否则检查对应 `.part` 文件，给出可恢复 offset。
4. 返回接受决定与 offset。
5. `stream_receive_file_cancellable` 从该位置写临时文件，限制读取量，不接受声明大小之前的意外 EOF。
6. 写完后 flush，重新读取临时文件计算完整 SHA-256；不一致则删除 `.part` 并报错。
7. 检查取消状态及目标文件冲突，把临时文件 rename 为目标文件。
8. 返回 completion ACK，再更新完成状态并发出事件。

**不能提前宣布成功的三个节点：**发送端 write_all 返回、发送端 finish 返回、接收端收齐声明字节数。它们都不等于“接收文件已完整校验并完成业务提交”。

同时也不要过度承诺：代码使用 flush + rename，不能据此宣称具备断电持久性、目录 fsync 保证或跨平台绝对原子事务。路径检查也不等于完整文件系统安全审计。

源码：[incoming.rs：handle_incoming_file_after_offer](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/transfer_operations/incoming.rs)、[receiver.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-transfer/src/receiver.rs)。

## 9. 断线恢复：业务身份与连接身份必须分开

`TransferIdentity` 保存 peer ID 和 transfer ID；`TransferSession` 不保存 QUIC Connection 或 Relay socket。`ResumableTransfer` 是某次尝试的载体，可以附带当前 Session 的 wire key。

```text
一项文件业务：同一 transfer ID + peer ID
    第一次尝试：连接 A，发送一部分
        ↓ 路径失效，业务 Paused
    第二次尝试：连接 B，重新协商 offset，再发送
```

`resume_transfers_for_peer` 在新连接建立后领取暂停传输、重新选择 PathLease、再派发。**这是应用层恢复，不应混称 QUIC 协议自身的 connection migration。**

还要注意两处细节：

- 逻辑身份描述含 peer ID，但当前 `TransferManager` 内部容器是以 transfer ID 为键的 `HashMap<String, TransferSession>`，再在状态中保存和检查 peer。不能凭结构名声称底层 map 已经直接使用二元组键。
- `confirmed_offset` 的命名不等于每次进度都经过远端落盘确认。发送路径也会更新本地发送进度；直连重试时仍要重新读取接收端 decision 的 offset，不能只信 UI 的百分比。

### 完成 ACK 丢失怎么办？

接收端可能已经校验并 rename，但发送端未收到 ACK。再次连接后，`existing_completed_file` 检查目标文件大小和 SHA-256，一致就返回完整大小作为 offset，并重新发送 completion。

这是对“内容已提交但确认丢失”场景的幂等恢复设计，不是对所有业务、所有进程崩溃情况的 exactly-once 保证。

### 应用被杀后是否能自动恢复全部任务？

不能仅凭这些代码下结论。`TransferManager` 是进程内状态；`.part` 在文件系统上存在，但“临时文件还在”不等于任务清单、身份配置、审批状态和重启恢复流程都持久化了。本文核实的是跨连接恢复机制，整应用重启恢复能力应另查调用链并实测。

源码：[transfer.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/transfer.rs)、[manager.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-transfer/src/manager.rs)、[resume.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/transfer_operations/resume.rs)。

## 10. 内存、背压与取消：需要讲清保证边界

### 流式读取不是“总内存永远只有一个 buffer”

当前 Rust `DEFAULT_TRANSFER_BUFFER` 为 **512 KiB**，用于分块处理。它不同于旧版 Dart/SFTP 优化中出现过的 256 KiB，不能把两个实现混起来。

流式处理避免把整个文件一次性读入业务内存，但总内存还包括并发任务、QUIC/TLS 缓冲、事件、哈希缓冲及系统缓存。buffer 大小不是峰值 RSS。

### 为什么进度事件也需要背压？

直连进度队列容量为 64，发送端在块处理后 `tx.send(...).await`。如果消费者持续落后，生产者会等待，避免无界积压。

代价是进度消费者太慢可能拖慢传输。可以讨论采样或合并进度的替代方案，但不能说当前已经实现全部优化，也不能把该队列容量推广成整个 SDK 所有队列容量。

### 取消是否立即生效？

流式循环在块边界检查 cancellation；这与“每个 await 都能立即中断”不同。例如正在等待网络写入或进度队列时，仅设置一个标志并不自动打断那个 await。任务 supervisor、连接关闭及底层 I/O 如何共同完成取消，需要沿调用链检查。

因此应回答：“有协作式取消检查与任务管理；我还需要通过阻塞写入和慢消费者测试确认最坏取消延迟”，而不是“取消按钮按下就立刻停止所有工作”。

源码：[sender.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-transfer/src/sender.rs)、[receiver.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-transfer/src/receiver.rs)、[transfer.rs：TRANSFER_PROGRESS_QUEUE_CAPACITY](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/transfer.rs)。

## 11. 故障矩阵：源码能说明什么，仍需验证什么？

| 场景 | 当前能从代码确认的机制 | 不能直接声称的结论 / 建议验证 |
| --- | --- | --- |
| 候选地址无法连通 | 分阶段、限时尝试与条件式 Relay 回退 | 不能保证任意 NAT 都可穿透；做隔离测试环境下的 direct/relay 场景测试 |
| 多个候选同时成功 | single-winner admission，拒绝迟到候选 | 不等于所有竞态已消除；制造不同握手完成顺序 |
| 文件中途断线 | 瞬时错误可进入 Paused，下一条兼容路径重新协商 offset | 不能承诺零丢失零重传；验证接收端实际文件与恢复位置 |
| 完成 ACK 丢失 | 检查已完成目标文件哈希，再确认完成 | 不等于任意操作 exactly-once；验证不会多生成一份文件 |
| `.part` 大小超出 manifest | offset 回退或校验拒绝 | 不能信任任意旧 partial；覆盖不匹配和内容损坏 |
| 源文件在恢复前变化 | 重建 manifest 并比较 | 不是发送期间的文件快照隔离 |
| 接收内容损坏 | 完整 SHA-256 比较，不匹配则删除临时文件 | 哈希不是用户授权，也不能代替身份认证 |
| 进度消费很慢 | 有界队列的 await 背压 | 不等于总内存有固定上限；测并发和取消延迟 |
| 接收目标已存在但内容不同 | 接收路径拒绝直接覆盖 | 不要承诺自动重命名策略，需查产品层逻辑 |
| 应用/设备突然终止 | 本文确认了内存状态与 `.part` 分离 | 未证明重启后自动恢复或断电安全 |

仓库已有相关测试源码，例如 `two_runtimes_authenticate_and_transfer_a_verified_file`、`two_runtimes_transfer_binary_boundary_matrix_is_verified_end_to_end`、`file_transfer_resumes_across_a_fresh_connection`。**本文是源码导读，本轮没有运行这些测试，也没有完成真机网络故障验证。**

测试入口：[direct_transfer_matrix.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/tests/runtime_integration/direct_transfer_matrix.rs)、[file_transfer_recovery.rs](https://github.com/hejulian2004/ssh_mobile/blob/5aba1d83405d53bdabd3807c76139489d17d7e6a/native/network_core/crates/network-core/src/tests/runtime_integration/file_transfer_recovery.rs)。

## 12. 十个值得准备的面试追问

### Q1：用了 Quinn，你自己的工程价值在哪里？

项目层的价值可以来自设备身份、业务协议、路径与能力适配、跨语言接口、失败恢复和可观测性。回答个人贡献时，只选择自己真实理解并参与的部分。不能把项目的所有机制自动归为个人独立设计。

### Q2：为什么文件需要业务 ACK，QUIC 已经可靠了？

传输可靠性说明字节传送问题，不能证明对端业务已做完哈希校验、文件提交与状态更新。业务 ACK 表达另一个层次的完成条件。即便对端提交成功，ACK 仍可能丢失，所以还需要幂等恢复。

### Q3：为什么不让 transfer ID 就等于 session ID？

文件业务可能跨多个连接重试，连接替换不应让业务身份消失。否则断线后难以关联原始 manifest 和 partial。当前 Session key 只用于某次尝试的任务与加密上下文。

### Q4：QUIC 加密了，为什么还做设备认证？

加密通道回答“途中能否被随意读取和篡改”，可信身份回答“对面是不是预期设备”。本项目临时证书不是公网 CA 身份凭据，所以额外用 pinned Ed25519 proof，并绑定 TLS exporter。

### Q5：Relay 与直连是不是共用完全相同的线协议？

不是。它们共享业务概念和管理边界，但直连文件用 QUIC 双向 stream 的 offer/decision/data/completion，Relay 用 reservation 数据面、应用信封、加密分块与完成消息。统一 SDK 不等于底层字节格式相同。

### Q6：为什么恢复后还要整文件 SHA-256？

offset 只能表示位置，不能证明已有前缀正确；整文件哈希用于检查拼接后内容。但重新读整个文件有 I/O 成本。若讨论分块哈希优化，要明确这是备选方案，不是当前已实现事实。

### Q7：能否说 QUIC 解决了一切队头阻塞？

不能。多个流可以独立组织数据，但同一流仍有顺序语义，各流也共享连接级拥塞和资源。应用若把所有消息串行等待，依然会形成自己的阻塞。应结合当前消息流与文件流分离设计说明。

### Q8：选择可靠流能力后，TCP 一定能发文件吗？

不能只看 profile。还要看业务 dispatcher 是否实现该 transport 的适配。当前文件 dispatcher 只明确分派 QUIC 与 Relay WebSocket。抽象能力与实现覆盖面需要分别核实。

### Q9：目前性能优化的代价是什么？

流式读写降低整文件预加载风险；有界队列限制积压但会反向影响生产速度；完整哈希增加磁盘读取；按需建连减少常驻资源但增加首次操作等待。没有统一基线时不报提升比例。

### Q10：不用 AI，你会怎样验证一项网络修改？

先写行为约束和失败输入，再定位对应函数；用 fake reader/writer 或本地双 runtime 观察事件、状态、文件和资源释放；最后跑相关回归。要准备一个自己实际完成的例子，而不是只背测试策略。

## 13. 建议亲手完成的三个小实验

**实验 A：ACK 丢失。**先用测试替身让接收端文件校验并提交成功，再阻止 completion 到达发送端。恢复连接后检查内容相同、没有重复文件、发送端最终正确结束。禁止通过破坏真实生产网络验证。

**实验 B：慢进度消费者。**只在测试环境降低进度消费速度，观察有界队列等待、传输吞吐、内存及取消行为。写下“观察到的结果”和“尚未解释的现象”，不要从容量直接计算真实总内存。

**实验 C：源文件变化。**暂停传输后修改源内容，再尝试恢复。检查 manifest 不一致时是否停止，是否避免把新旧内容拼接成成功文件。把恢复前变化和发送期间变化当成两个不同测试。

每个实验最后只交四项材料：入口函数、预期行为、实际证据、仍未覆盖的边界。能讲清这四项，比背出十个 crate 名更有说服力。
