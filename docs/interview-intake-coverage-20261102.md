# 用户面经补充：收录、去重与逐项覆盖记录

整理日期：2026-11-02。用户提供面经线索/日期未核；非公司官方题库，不进入2023-10-30至2026-10-30检索来源、公司或频次统计。

本批新增 **57 道深化练习**，补充 **14 道既有答案**，原491道题的路径与题号保留；网站解析后的总题数为 **548 道**。数量是内容规模，不是招聘频率、命中率或真实公司原题数量。

## 学习入口

- [Android缓存、网络与设备场景](interview-intake-android-20261102.md)：15题。
- [Java、并发与工程设计](interview-intake-java-systems-20261102.md)：17题。
- [网络与跨端运行时](interview-intake-network-runtime-20261102.md)：17题。
- [算法演练](interview-intake-algorithms-20261102.md)：8题。

每道新题均有口述答案、原理边界、带答案的追问、易错点与官方/原始依据；算法另有Java示例、复杂度与边界验证。重复基础概念链接旧题，不再制造同义题。

## 素材与统计边界

- 九份文字面经和十三张截图均已检查题意。截图中一张与另一张完全相同，独立图片十二张。
- 腾讯地图的文字与两张截图合为同一个来源组；字节生服的文字与两张截图也合为一组；两张相同截图合为一组。最终十五个来源组。连续多页截图作为同一篇线索，而非多份独立面经。
- 原帖URL、可靠面试日期、发帖日期均未取得；公司/轮次只是用户所提供材料中的自述。百度图的2026/4/8、字节图的2025/7/24为笔记时间，小鹏的标签#24也不作为面试年份。
- 小米截图来自面试服务类账号的二手整理，不是已认证亲历，不用于企业原题背书。字节MVVM文本带转载整理口吻，亦未独立认证。
- 原有Q/S三年检索统计保持116道来源归纳题、27份正式来源、20家公司/招聘品牌；本批U编号只在本收录记录内使用，不作为已核S来源。
- 未上传截图、账号水印或原帖全文。只保存题意归纳、原创参考答案和学习导航；编辑性追问不冒充原面试追问。

## 准备框架

自我介绍用约60秒说明真实教育背景、目标岗位、最熟悉项目、一个可验证的个人贡献。可到岗日期、每周天数和持续月数由本人填写，不从“研一”推定。反问聚焦业务、导师与技术栈、实习任务及工作安排。

共享屏幕前准备“入口→状态/业务→数据/网络→结果回传”的调用链，能解释包职责、异常出口、资源释放和一个设计取舍。AI辅助代码按自己提出需求、核查、调试、修改与验证的真实参与边界说明；不把生成代码等同于独立设计底层协议。可继续练习[AI代码接管练习册](ai-code-takeover-workbook.md)。

演示前在目标设备验证登录、接口和弱网失败；准备明确标识的可控测试数据或录屏作为补充，接口失效时展示错误处理与恢复过程，不把mock演示冒充真实服务端成功。

秒杀、短链、新闻App、智能音量、机器人硬件、论文和原帖实习，均是分享者的背景。没有对应用户源码与事实时，只按“需求/约束→数据与状态→并发/失败→验证”练习设计。秒杀框架要说明库存扣减的一致性、幂等、限流、支付/取消及补偿；论文要由本人补题目、方法、贡献、实验和局限，不能代写个人经历。

## 待澄清清单

- “MVP模板代码是指”原文残缺，不能生成确定原答。
- “ViewModel直接get值”未给代码：已有Q069只解释快照读取、订阅、线程和postValue时机，不宣称直接get一律错误。
- “实习节假日三级数据源”未说明哪三级，不擅自回答成内存/磁盘/网络。
- 论文题目、多线程应用题的条件、未知的原生路由插件名称均缺失；保留通用练习或核对框架，不还原未知题。
- “C调用堆栈/Java调用更快或更慢”需先分清分配、访问与函数调用；“Flutter没有动态化能力”须先限定平台和运行模式。
- iOS掌握程度、行业前景与业务路线属于能力边界或观点，不编项目和确定行业预测。

## 覆盖口径

共 **252 条归纳议题记录**。一条可能合并原材料中连续的同一追问；多个来源的同一知识点仍各有映射，但不重复新建题目。

| 处理方式 | 议题记录数 | 含义 |
|---|---:|---|
| 新题深化 | 127 | 指向至少一道本批深化题，必要时同时关联旧题 |
| 扩充已有 | 30 | 指向本批补充过的原有Q/E题 |
| 既有导航 | 76 | 现有内容已覆盖，保留学习路径 |
| 准备框架 | 15 | 个人事实、演示或观点准备，不虚构经历 |
| 待澄清 | 4 | 原材料缺必要上下文；可能另给通用练习 |

## 来源组总表

| ID | 材料题名线索 | 输入 | 议题数 | 说明 |
|---|---|---|---:|---|
| U01 | 研0小厂 Android 实习 | T01 | 20 | 原帖URL、日期及真实性未核 |
| U02 | 影石 Android 一面 | T02 | 21 | 原帖URL、日期及真实性未核 |
| U03 | 蚂蚁客户端移动端一面 | T03 | 13 | 原帖URL、日期及真实性未核 |
| U04 | 字节客户端MVVM与协程一面 | T04 | 6 | 转载整理口吻；未认证亲历或来源身份。 |
| U05 | 同花顺提前批 Android 一面 | T05 | 16 | 原帖自述Java转Android面试；不得当作岗位统一题纲。 |
| U06 | 影石 Android 二面 | T06 | 16 | 原帖URL、日期及真实性未核 |
| U07 | 腾讯地图客户端一面 | T07、IMG-E | 11 | 文字与两张截图为同份线索，只计一个来源组。 |
| U08 | 字节生服客户端日常实习一面 | T08、IMG-G | 23 | 两张截图与文字同份；GET/POST/PUT和git merge为文字补充，保留。 图中2025/7/24仅笔记时间，不作为面试日期。 |
| U09 | 米哈游26提前批移动客户端一面 | T09 | 19 | 校招届别不替代真实面试日期；原编号缺1不补造。 |
| U10 | 百度网盘 Android 实习截图 | IMG-A | 7 | 图中记事本2026/4/8仅笔记时间，不认定面试日期；原编号重复不补造。 |
| U11 | 滴滴青桔 Android 二面截图 | IMG-B | 25 | 原帖URL、日期及真实性未核 |
| U12 | 小鹏 Android 一面截图 | IMG-C | 19 | 标题标签#24不能证明面试年份。 |
| U13 | 未标公司 Flutter/Android 连续三页截图 | IMG-D | 20 | 公司、日期未知；末尾截断不补题。 |
| U14 | 未标公司客户端面经重复截图 | IMG-F1、IMG-F2 | 14 | 第9、10张像素与SHA相同，合并为一个素材组，不重复计证据。 |
| U15 | 小米高级Android服务账号整理图 | IMG-H | 22 | 面试服务类账号的二手总结，不能据此确认小米真实原题、面试轮次或频率。 |

## 每份材料的逐项学习映射

## U01 研0小厂 Android 实习

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U01-01 | 自我介绍与可实习时间 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U01-02 | 项目背景与个人贡献 | 既有导航 | [HI01](android-interview-handbook.md#q-i01)、[HC01](android-interview-handbook.md#q-c01)、[PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U01-03 | 本地歌曲、播放缓存与远程URL缓存 | 新题深化 | [media-cache](interview-intake-android-20261102.md#ad01) | — |
| U01-04 | Hilt注入缓存与作用域 | 新题深化 | [hilt-cache](interview-intake-android-20261102.md#ad02) | — |
| U01-05 | MVVM分层职责 | 扩充已有 | [Q066](../questions/10-Jetpack架构与存储/Q066-MVC、MVP、MVVM-如何划分职责.md)、[HC05](android-interview-handbook.md#q-c05) | — |
| U01-06 | 自定义View实现步骤 | 既有导航 | [Q022](../questions/03-View绘制与触摸/Q022-自定义-View-怎样兼顾正确测量与绘制性能.md) | — |
| U01-07 | 触摸事件分发 | 既有导航 | [Q019](../questions/03-View绘制与触摸/Q019-触摸事件分发与拦截的职责如何划分.md)、[Q020](../questions/03-View绘制与触摸/Q020-父容器中途拦截手势时子-View-会发生什么.md) | — |
| U01-08 | 冷流、热流、StateFlow与SharedFlow | 既有导航 | [E015](../supplements/06-Kotlin与协程/E015-StateFlow-与-SharedFlow-怎么选择.md)、[KT30](kotlin-coroutines-interview-guide.md#kt30)、[KT33](kotlin-coroutines-interview-guide.md#kt33)、[KT34](kotlin-coroutines-interview-guide.md#kt34) | — |
| U01-09 | 观察者模式及与Flow关系 | 新题深化 | [observer](interview-intake-java-systems-20261102.md#js04) | — |
| U01-10 | ViewPager嵌套RecyclerView冲突 | 新题深化 | [pager-conflict](interview-intake-android-20261102.md#ad03) | — |
| U01-11 | 按可用宽度自适应瀑布流 | 新题深化 | [adaptive-grid](interview-intake-android-20261102.md#ad04) | — |
| U01-12 | OkHttp封装与Cookie自动发送 | 新题深化 | [network-layer](interview-intake-android-20261102.md#ad05)、[cookie](interview-intake-android-20261102.md#ad07) | — |
| U01-13 | 网络代理配置 | 新题深化 | [proxy](interview-intake-android-20261102.md#ad08) | — |
| U01-14 | OkHttp阻塞与协程适配 | 新题深化 | [okhttp-cancel](interview-intake-android-20261102.md#ad09)、[KT40](kotlin-coroutines-interview-guide.md#kt40) | — |
| U01-15 | 成功、业务失败、异常到Result和UiState | 新题深化 | [result-layer](interview-intake-android-20261102.md#ad06)、[KT06](kotlin-coroutines-interview-guide.md#kt06) | — |
| U01-16 | Repository重复错误与拦截器边界 | 新题深化 | [result-layer](interview-intake-android-20261102.md#ad06) | — |
| U01-17 | Set-Cookie保存与并发安全 | 新题深化 | [cookie](interview-intake-android-20261102.md#ad07) | — |
| U01-18 | 源码如何生成APK | 新题深化 | [apk](interview-intake-android-20261102.md#ad10) | — |
| U01-19 | 项目演示遇第三方接口故障 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | 准备可控演示与失败路径；不认定用户项目发生过 |
| U01-20 | 反问业务、工作时间与薪资 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |

## U02 影石 Android 一面

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U02-01 | 进程间通信 | 既有导航 | [Q015](../questions/02-Handler线程与IPC/Q015-Binder-如何完成一次跨进程调用.md)、[HC32](android-interview-handbook.md#q-c32) | — |
| U02-02 | HTTP/HTTPS与TLS握手 | 新题深化 | [tls](interview-intake-network-runtime-20261102.md#nt07) | — |
| U02-03 | 单例工厂与非懒加载单例 | 新题深化 | [dcl](interview-intake-java-systems-20261102.md#js02)、[patterns](interview-intake-java-systems-20261102.md#js04) | — |
| U02-04 | TCP三次握手原因 | 新题深化 | [tcp-syn](interview-intake-network-runtime-20261102.md#nt08) | — |
| U02-05 | TCP与UDP比较 | 新题深化 | [osi-udp](interview-intake-network-runtime-20261102.md#nt17) | — |
| U02-06 | HashMap、ConcurrentHashMap与树化 | 扩充已有 | [Q035](../questions/07-Java集合与JVM/Q035-HashMap-如何定位元素并处理冲突和扩容.md)、[Q036](../questions/07-Java集合与JVM/Q036-ConcurrentHashMap-如何支持并发访问.md)、[JA29](java-core-interview-guide.md#ja29) | — |
| U02-07 | ArrayList原理与线程安全 | 扩充已有 | [Q037](../questions/07-Java集合与JVM/Q037-ArrayList-为什么查询快而中间插入可能昂贵.md)、[JA30](java-core-interview-guide.md#ja30) | — |
| U02-08 | 虚拟内存 | 新题深化 | [vm-os](interview-intake-java-systems-20261102.md#js07) | — |
| U02-09 | 垃圾回收 | 既有导航 | [Q040](../questions/07-Java集合与JVM/Q040-垃圾回收怎样判断对象是否仍然存活.md)、[JA24](java-core-interview-guide.md#ja24)、[JA37](java-core-interview-guide.md#ja37) | — |
| U02-10 | public与static | 新题深化 | [public-types](interview-intake-java-systems-20261102.md#js06) | — |
| U02-11 | 线程池参数与使用场景 | 扩充已有 | [Q051](../questions/08-并发与线程安全/Q051-线程池参数怎样共同决定任务执行.md)、[JA21](java-core-interview-guide.md#ja21)、[JA22](java-core-interview-guide.md#ja22) | — |
| U02-12 | 核心与非核心工作线程 | 扩充已有 | [Q051](../questions/08-并发与线程安全/Q051-线程池参数怎样共同决定任务执行.md) | — |
| U02-13 | synchronized锁对象与static方法 | 既有导航 | [Q048](../questions/08-并发与线程安全/Q048-synchronized-锁住的是哪个对象.md) | — |
| U02-14 | 二叉树类别 | 新题深化 | [tree-taxonomy](interview-intake-algorithms-20261102.md#al07) | — |
| U02-15 | ThreadLocal | 既有导航 | [JA31](java-core-interview-guide.md#ja31) | — |
| U02-16 | 快速排序 | 新题深化 | [quick-sort](interview-intake-algorithms-20261102.md#al02) | — |
| U02-17 | 异常捕获边界与锁释放 | 既有导航 | [JA14](java-core-interview-guide.md#ja14)、[JA15](java-core-interview-guide.md#ja15)、[JA27](java-core-interview-guide.md#ja27) | — |
| U02-18 | C++指针与引用 | 新题深化 | [cpp-ref](interview-intake-java-systems-20261102.md#js08) | — |
| U02-19 | volatile | 既有导航 | [Q047](../questions/08-并发与线程安全/Q047-volatile-保证什么，为什么不能保证自增原子性.md)、[JA16](java-core-interview-guide.md#ja16)、[JA17](java-core-interview-guide.md#ja17) | — |
| U02-20 | 线程中断 | 既有导航 | [JA20](java-core-interview-guide.md#ja20)、[JA32](java-core-interview-guide.md#ja32) | — |
| U02-21 | 多线程顺序执行 | 新题深化 | [thread-order](interview-intake-java-systems-20261102.md#js05) | — |

## U03 蚂蚁客户端移动端一面

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U03-01 | 面试官介绍、自我介绍 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U03-02 | Flutter、RN与原生绘制差别 | 新题深化 | [render-platforms](interview-intake-network-runtime-20261102.md#nt01) | — |
| U03-03 | Flutter、RN与Java线程模型 | 新题深化 | [thread-platforms](interview-intake-network-runtime-20261102.md#nt02) | — |
| U03-04 | Java与C堆栈比较 | 新题深化 | [heap-stack](interview-intake-network-runtime-20261102.md#nt04) | — |
| U03-05 | TS执行模型和宏任务微任务 | 新题深化 | [js-loop](interview-intake-network-runtime-20261102.md#nt03) | — |
| U03-06 | C堆栈速度原话含糊 | 新题深化 | [heap-stack](interview-intake-network-runtime-20261102.md#nt04) | 先区分分配成本、调用、局部性；不存在固定倍数 |
| U03-07 | Java调用速度原话含糊 | 新题深化 | [heap-stack](interview-intake-network-runtime-20261102.md#nt04) | 需要具体代码和运行时条件 |
| U03-08 | Flutter动态化能力边界 | 新题深化 | [compile-modes](interview-intake-network-runtime-20261102.md#nt05) | — |
| U03-09 | JIT、AOT、解释执行 | 新题深化 | [compile-modes](interview-intake-network-runtime-20261102.md#nt05) | — |
| U03-10 | 语言与运行模式的关系 | 新题深化 | [compile-modes](interview-intake-network-runtime-20261102.md#nt05) | — |
| U03-11 | JS/TS虚拟机与运行方式 | 新题深化 | [js-loop](interview-intake-network-runtime-20261102.md#nt03)、[compile-modes](interview-intake-network-runtime-20261102.md#nt05) | — |
| U03-12 | DEX设计及与class区别 | 新题深化 | [dex](interview-intake-network-runtime-20261102.md#nt06) | — |
| U03-13 | 反转链表 | 既有导航 | [Q096](../questions/15-数据结构与算法/Q096-如何原地反转单链表.md) | 帖子算法回忆不确定；按明确提及题名作练习导航 |

## U04 字节客户端MVVM与协程一面

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U04-01 | 项目MVVM层持有关系 | 扩充已有 | [Q066](../questions/10-Jetpack架构与存储/Q066-MVC、MVP、MVVM-如何划分职责.md) | 修正双向持有View说法 |
| U04-02 | ViewModel配置重建保留与ViewModelStoreOwner | 扩充已有 | [Q068](../questions/10-Jetpack架构与存储/Q068-ViewModel-为什么能跨配置变化保留状态.md)、[PL01](android-platform-interview-guide.md#ad01) | — |
| U04-03 | cancel后是否立刻停止 | 扩充已有 | [E016](../supplements/06-Kotlin与协程/E016-为什么取消协程后-CPU-循环仍可能继续.md)、[KT22](kotlin-coroutines-interview-guide.md#kt22) | — |
| U04-04 | 不检查取消的子任务与父任务 | 扩充已有 | [E014](../supplements/06-Kotlin与协程/E014-结构化并发和-Supervisor-有什么不同.md)、[E016](../supplements/06-Kotlin与协程/E016-为什么取消协程后-CPU-循环仍可能继续.md)、[KT24](kotlin-coroutines-interview-guide.md#kt24) | — |
| U04-05 | 协程有栈/无栈与Continuation状态机 | 扩充已有 | [Q033](../questions/06-Kotlin与协程/Q033-挂起函数怎样保存和恢复执行状态.md) | — |
| U04-06 | 零钱兑换II | 新题深化 | [coin-change](interview-intake-algorithms-20261102.md#al04) | — |

## U05 同花顺提前批 Android 一面

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U05-01 | 自介与项目介绍 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U05-02 | 共享屏幕源码讲解及包职责 | 新题深化 | [source-ai](interview-intake-java-systems-20261102.md#js16) | — |
| U05-03 | 注解SOURCE/CLASS/RUNTIME策略 | 新题深化 | [annotation](interview-intake-java-systems-20261102.md#js01) | — |
| U05-04 | 密码加盐 | 新题深化 | [password](interview-intake-java-systems-20261102.md#js10) | — |
| U05-05 | MD5碰撞与替代 | 新题深化 | [password](interview-intake-java-systems-20261102.md#js10) | — |
| U05-06 | 缓存key、内容和失效 | 新题深化 | [media-cache](interview-intake-android-20261102.md#ad01)、[cache-expiry](interview-intake-java-systems-20261102.md#js11) | — |
| U05-07 | CDN | 新题深化 | [cdn](interview-intake-network-runtime-20261102.md#nt13) | — |
| U05-08 | 项目设计模式 | 新题深化 | [patterns](interview-intake-java-systems-20261102.md#js04)、[observer](interview-intake-java-systems-20261102.md#js04) | — |
| U05-09 | 扩展上传实现 | 新题深化 | [upload-extension](interview-intake-java-systems-20261102.md#js03) | — |
| U05-10 | 开闭与里氏替换原则 | 新题深化 | [upload-extension](interview-intake-java-systems-20261102.md#js03) | — |
| U05-11 | 单例 | 新题深化 | [dcl](interview-intake-java-systems-20261102.md#js02) | — |
| U05-12 | 双重检查的两次判断 | 新题深化 | [dcl](interview-intake-java-systems-20261102.md#js02) | — |
| U05-13 | volatile与DCL发布 | 新题深化 | [dcl](interview-intake-java-systems-20261102.md#js02) | — |
| U05-14 | AI工具与AI编码IDE | 新题深化 | [source-ai](interview-intake-java-systems-20261102.md#js16)、[FL52](flutter-interview-guide.md#q52) | — |
| U05-15 | 实习贡献追问 | 既有导航 | [HI01](android-interview-handbook.md#q-i01)、[HI08](android-interview-handbook.md#q-i08)、[HI14](android-interview-handbook.md#q-i14)、[PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U05-16 | 反问岗位背景与意愿 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |

## U06 影石 Android 二面

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U06-01 | 快速排序 | 新题深化 | [quick-sort](interview-intake-algorithms-20261102.md#al02) | — |
| U06-02 | 项目秒杀逻辑 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | 他人项目背景，不推定用户做过；按一致性/并发/恢复框架准备 |
| U06-03 | 论文相关 | 待澄清 | [ASK](interview-intake-coverage-20261102.md#待澄清清单) | 缺论文题目和研究内容 |
| U06-04 | IPC | 既有导航 | [Q015](../questions/02-Handler线程与IPC/Q015-Binder-如何完成一次跨进程调用.md) | — |
| U06-05 | LRU淘汰 | 既有导航 | [Q108](../questions/15-数据结构与算法/Q108-怎样设计-LRU-缓存.md) | — |
| U06-06 | 线程池使用场景 | 扩充已有 | [Q051](../questions/08-并发与线程安全/Q051-线程池参数怎样共同决定任务执行.md)、[JA21](java-core-interview-guide.md#ja21) | — |
| U06-07 | TCP握手与不能两次 | 新题深化 | [tcp-syn](interview-intake-network-runtime-20261102.md#nt08) | — |
| U06-08 | C++掌握程度 | 新题深化 | [cpp-ref](interview-intake-java-systems-20261102.md#js08)、[PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U06-09 | 未给题目的多线程应用题 | 待澄清 | [thread-order](interview-intake-java-systems-20261102.md#js05)、[ASK](interview-intake-coverage-20261102.md#待澄清清单) | 只补通用练习，不还原未知原题 |
| U06-10 | 逻辑过期处理缓存击穿 | 新题深化 | [cache-expiry](interview-intake-java-systems-20261102.md#js11) | — |
| U06-11 | 锁使用 | 既有导航 | [Q048](../questions/08-并发与线程安全/Q048-synchronized-锁住的是哪个对象.md)、[Q053](../questions/08-并发与线程安全/Q053-ReentrantLock-相比-synchronized-多了哪些控制能力.md)、[Q055](../questions/08-并发与线程安全/Q055-乐观锁与悲观锁应怎样选择.md) | — |
| U06-12 | CPU调度 | 新题深化 | [cpu-schedule](interview-intake-java-systems-20261102.md#js17) | — |
| U06-13 | OSI七层 | 新题深化 | [osi-udp](interview-intake-network-runtime-20261102.md#nt17) | 只作网络模型，不暗示所有现代协议严格一一对应 |
| U06-14 | 死锁条件 | 既有导航 | [Q054](../questions/08-并发与线程安全/Q054-死锁的必要条件与排查方式是什么.md) | — |
| U06-15 | 内存泄漏与检测 | 既有导航 | [Q074](../questions/11-性能与稳定性/Q074-内存泄漏与-OOM-是什么关系.md)、[JA38](java-core-interview-guide.md#ja38)、[PL35](android-platform-interview-guide.md#ad35) | — |
| U06-16 | 二叉树最近公共祖先 | 新题深化 | [lca](interview-intake-algorithms-20261102.md#al05) | — |

## U07 腾讯地图客户端一面

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U07-01 | Java线程安全与synchronized | 既有导航 | [Q048](../questions/08-并发与线程安全/Q048-synchronized-锁住的是哪个对象.md)、[JA16](java-core-interview-guide.md#ja16)、[JA18](java-core-interview-guide.md#ja18) | — |
| U07-02 | Flutter线程安全 | 新题深化 | [thread-platforms](interview-intake-network-runtime-20261102.md#nt02)、[FL12](flutter-interview-guide.md#q12) | — |
| U07-03 | TCP/IP特点与分层 | 新题深化 | [osi-udp](interview-intake-network-runtime-20261102.md#nt17) | — |
| U07-04 | TCP拥塞控制 | 新题深化 | [congestion](interview-intake-network-runtime-20261102.md#nt10) | — |
| U07-05 | MVC与MVVM | 扩充已有 | [Q066](../questions/10-Jetpack架构与存储/Q066-MVC、MVP、MVVM-如何划分职责.md) | — |
| U07-06 | MVVM项目应用 | 既有导航 | [HC04](android-interview-handbook.md#q-c04)、[HC05](android-interview-handbook.md#q-c05) | — |
| U07-07 | ViewModel直接get值问题 | 扩充已有 | [Q069](../questions/10-Jetpack架构与存储/Q069-LiveData-如何做到生命周期感知.md) | 上下文未给；区分快照读取、订阅、线程与异步尚未提交 |
| U07-08 | IPC | 既有导航 | [Q015](../questions/02-Handler线程与IPC/Q015-Binder-如何完成一次跨进程调用.md) | — |
| U07-09 | Flutter优势与取舍 | 新题深化 | [render-platforms](interview-intake-network-runtime-20261102.md#nt01) | — |
| U07-10 | 最小k个数并升序 | 新题深化 | [smallest-k](interview-intake-algorithms-20261102.md#al03) | — |
| U07-11 | MVP模板代码含义不完整 | 待澄清 | [ASK](interview-intake-coverage-20261102.md#待澄清清单) | 原图原话残缺，不生成猜测标准答案 |

## U08 字节生服客户端日常实习一面

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U08-01 | 排序类别与复杂度最好最坏 | 新题深化 | [sort-taxonomy](interview-intake-algorithms-20261102.md#al01)、[quick-sort](interview-intake-algorithms-20261102.md#al02) | — |
| U08-02 | 单例、责任链、模板、工厂 | 新题深化 | [patterns](interview-intake-java-systems-20261102.md#js04)、[dcl](interview-intake-java-systems-20261102.md#js02) | — |
| U08-03 | 责任链项目用途 | 新题深化 | [patterns](interview-intake-java-systems-20261102.md#js04) | — |
| U08-04 | 单例与全局变量 | 新题深化 | [dcl](interview-intake-java-systems-20261102.md#js02) | — |
| U08-05 | synchronized | 既有导航 | [Q048](../questions/08-并发与线程安全/Q048-synchronized-锁住的是哪个对象.md) | — |
| U08-06 | 进程与线程 | 既有导航 | [Q081](../questions/12-Framework与系统/Q081-进程和线程的资源边界有什么不同.md) | — |
| U08-07 | 堆栈用途与必要性 | 新题深化 | [heap-stack](interview-intake-network-runtime-20261102.md#nt04) | — |
| U08-08 | URL到网页与相关协议 | 新题深化 | [Q060](../questions/09-网络与网络库/Q060-从输入-URL-到收到响应会经历哪些步骤.md)、[cdn](interview-intake-network-runtime-20261102.md#nt13)、[tls](interview-intake-network-runtime-20261102.md#nt07) | — |
| U08-09 | HTTPS加密算法 | 新题深化 | [tls](interview-intake-network-runtime-20261102.md#nt07) | — |
| U08-10 | GET、POST、PUT用途差别 | 新题深化 | [http-methods](interview-intake-network-runtime-20261102.md#nt12) | — |
| U08-11 | 项目来源、背景和结果 | 新题深化 | [PREP](interview-intake-coverage-20261102.md#准备框架)、[source-ai](interview-intake-java-systems-20261102.md#js16) | — |
| U08-12 | QPS与性能测量 | 新题深化 | [qps](interview-intake-java-systems-20261102.md#js14) | — |
| U08-13 | 短链创建与布隆过滤器 | 新题深化 | [bloom-shortlink](interview-intake-java-systems-20261102.md#js13) | — |
| U08-14 | 短链写库失败 | 新题深化 | [bloom-shortlink](interview-intake-java-systems-20261102.md#js13) | — |
| U08-15 | 效果验证 | 新题深化 | [qps](interview-intake-java-systems-20261102.md#js14)、[Q115](../questions/16-工程设计与项目追问/Q115-怎样证明项目优化确实带来收益.md) | — |
| U08-16 | Redis防重复消费 | 新题深化 | [idempotency](interview-intake-java-systems-20261102.md#js12) | — |
| U08-17 | Redis与本地/数据库取舍 | 新题深化 | [idempotency](interview-intake-java-systems-20261102.md#js12) | — |
| U08-18 | Redis数据类型 | 新题深化 | [idempotency](interview-intake-java-systems-20261102.md#js12) | — |
| U08-19 | 部署与使用云中间件的理由 | 新题深化 | [qps](interview-intake-java-systems-20261102.md#js14) | — |
| U08-20 | 云Redis性能测试 | 新题深化 | [qps](interview-intake-java-systems-20261102.md#js14) | — |
| U08-21 | Git使用与merge | 既有导航 | [git-merge](android-interview-handbook.md#q-c35) | — |
| U08-22 | 反转链表 | 既有导航 | [Q096](../questions/15-数据结构与算法/Q096-如何原地反转单链表.md) | — |
| U08-23 | 矩阵最长递增路径 | 新题深化 | [matrix-lip](interview-intake-algorithms-20261102.md#al06) | — |

## U09 米哈游26提前批移动客户端一面

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U09-01 | HTTP1.0和HTTP2及头部 | 新题深化 | [http2](interview-intake-network-runtime-20261102.md#nt11) | — |
| U09-02 | TCP握手与第一次失败重试 | 新题深化 | [tcp-syn](interview-intake-network-runtime-20261102.md#nt08) | — |
| U09-03 | 为何三次握手 | 新题深化 | [tcp-syn](interview-intake-network-runtime-20261102.md#nt08) | — |
| U09-04 | 进程资源与线程切换成本 | 新题深化 | [Q081](../questions/12-Framework与系统/Q081-进程和线程的资源边界有什么不同.md)、[vm-os](interview-intake-java-systems-20261102.md#js07) | — |
| U09-05 | 进程崩溃是否影响其他进程 | 新题深化 | [Q081](../questions/12-Framework与系统/Q081-进程和线程的资源边界有什么不同.md)、[vm-os](interview-intake-java-systems-20261102.md#js07) | — |
| U09-06 | 线程切换指令与上下文 | 新题深化 | [vm-os](interview-intake-java-systems-20261102.md#js07) | 依CPU/OS实现，不能统一背某一条指令 |
| U09-07 | 多线程共享竞争本质与互斥 | 既有导航 | [JA16](java-core-interview-guide.md#ja16)、[JA18](java-core-interview-guide.md#ja18)、[Q048](../questions/08-并发与线程安全/Q048-synchronized-锁住的是哪个对象.md)、[Q053](../questions/08-并发与线程安全/Q053-ReentrantLock-相比-synchronized-多了哪些控制能力.md) | — |
| U09-08 | Java堆栈 | 新题深化 | [JA24](java-core-interview-guide.md#ja24)、[heap-stack](interview-intake-network-runtime-20261102.md#nt04) | — |
| U09-09 | GC算法和可达性 | 既有导航 | [Q040](../questions/07-Java集合与JVM/Q040-垃圾回收怎样判断对象是否仍然存活.md)、[JA37](java-core-interview-guide.md#ja37) | — |
| U09-10 | 循环引用与GC | 既有导航 | [Q040](../questions/07-Java集合与JVM/Q040-垃圾回收怎样判断对象是否仍然存活.md) | 追踪式GC不以引用计数是否归零判断 |
| U09-11 | StringBuffer与StringBuilder | 既有导航 | [JA04](java-core-interview-guide.md#ja04) | — |
| U09-12 | ArrayList并发和扩容 | 扩充已有 | [Q037](../questions/07-Java集合与JVM/Q037-ArrayList-为什么查询快而中间插入可能昂贵.md)、[JA30](java-core-interview-guide.md#ja30) | — |
| U09-13 | ConcurrentHashMap | 扩充已有 | [Q036](../questions/07-Java集合与JVM/Q036-ConcurrentHashMap-如何支持并发访问.md)、[JA29](java-core-interview-guide.md#ja29) | — |
| U09-14 | Java基本类型大小 | 新题深化 | [public-types](interview-intake-java-systems-20261102.md#js06) | — |
| U09-15 | Kotlin lazy线程安全 | 既有导航 | [KT08](kotlin-coroutines-interview-guide.md#kt08)、[KT16](kotlin-coroutines-interview-guide.md#kt16) | — |
| U09-16 | MVP和MVVM | 扩充已有 | [Q066](../questions/10-Jetpack架构与存储/Q066-MVC、MVP、MVVM-如何划分职责.md) | — |
| U09-17 | LiveData生命周期 | 扩充已有 | [Q069](../questions/10-Jetpack架构与存储/Q069-LiveData-如何做到生命周期感知.md) | — |
| U09-18 | 组件化 | 既有导航 | [Q114](../questions/16-工程设计与项目追问/Q114-组件化的边界和通信协议怎样设计.md) | — |
| U09-19 | 实际需求介绍 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |

## U10 百度网盘 Android 实习截图

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U10-01 | var与val | 既有导航 | [KT03](kotlin-coroutines-interview-guide.md#kt03) | — |
| U10-02 | !!、可空类型与安全调用 | 既有导航 | [KT01](kotlin-coroutines-interview-guide.md#kt01)、[KT02](kotlin-coroutines-interview-guide.md#kt02) | 原图单个?含义未指明，区分T?和?. |
| U10-03 | 常用UI布局 | 既有导航 | [ui-layouts](../questions/05-JetpackCompose/Q027-Compose-与-XML-View-的区别及选型依据.md) | — |
| U10-04 | 跨线程通信 | 既有导航 | [Q009](../questions/02-Handler线程与IPC/Q009-Handler、Looper-和-MessageQueue-如何协作.md)、[Q093](../questions/14-Flutter与跨端/Q093-Dart-的事件循环、异步与-isolate-是什么关系.md) | — |
| U10-05 | 四组件与下载放Service的条件 | 扩充已有 | [Q001](../questions/01-Android基础与生命周期/Q001-四大组件各自解决什么问题.md)、[Q007](../questions/01-Android基础与生命周期/Q007-Activity-和-Service-有什么区别.md)、[PL18](android-platform-interview-guide.md#ad18)、[PL19](android-platform-interview-guide.md#ad19) | — |
| U10-06 | Handler组成及子线程创建 | 扩充已有 | [Q009](../questions/02-Handler线程与IPC/Q009-Handler、Looper-和-MessageQueue-如何协作.md)、[Q014](../questions/02-Handler线程与IPC/Q014-HandlerThread-与普通-Thread-有何差别.md) | — |
| U10-07 | Kotlin协程宽泛问题 | 既有导航 | [Q032](../questions/06-Kotlin与协程/Q032-协程和线程是什么关系.md)、[KT18](kotlin-coroutines-interview-guide.md#kt18) | 未给更细追问，不将状态机归为该截图原题 |

## U11 滴滴青桔 Android 二面截图

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U11-01 | 自我介绍 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U11-02 | 后端实习职责 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | 原帖个人经历，不能替换用户经历 |
| U11-03 | 反编译工具与困难 | 新题深化 | [authorized-tools](interview-intake-java-systems-20261102.md#js15) | — |
| U11-04 | 证书校验安全边界 | 新题深化 | [authorized-tools](interview-intake-java-systems-20261102.md#js15)、[tls](interview-intake-network-runtime-20261102.md#nt07) | 只谈授权自有应用实验，不提供第三方绕过操作 |
| U11-05 | Frida与Xposed | 新题深化 | [authorized-tools](interview-intake-java-systems-20261102.md#js15) | — |
| U11-06 | Frida Hook机制和实验准备 | 新题深化 | [authorized-tools](interview-intake-java-systems-20261102.md#js15) | — |
| U11-07 | 环境音量采样与算法协作 | 新题深化 | [sensor-pipeline](interview-intake-android-20261102.md#ad14) | 需求、权限、采样、算法接口与功耗为框架；不编具体模型 |
| U11-08 | 低端机性能专项 | 既有导航 | [Q115](../questions/16-工程设计与项目追问/Q115-怎样证明项目优化确实带来收益.md)、[Q116](../questions/16-工程设计与项目追问/Q116-多机型兼容问题应怎样建立验证矩阵.md)、[PL33](android-platform-interview-guide.md#ad33) | — |
| U11-09 | 实习收获 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U11-10 | 源码到APK | 新题深化 | [apk](interview-intake-android-20261102.md#ad10) | — |
| U11-11 | 点图标启动 | 新题深化 | [app-start](interview-intake-android-20261102.md#ad15) | — |
| U11-12 | Handler | 既有导航 | [Q009](../questions/02-Handler线程与IPC/Q009-Handler、Looper-和-MessageQueue-如何协作.md) | — |
| U11-13 | Glide缓存 | 新题深化 | [glide](interview-intake-android-20261102.md#ad11) | — |
| U11-14 | LRU | 既有导航 | [Q108](../questions/15-数据结构与算法/Q108-怎样设计-LRU-缓存.md) | — |
| U11-15 | Looper不ANR与唤醒 | 既有导航 | [Q012](../questions/02-Handler线程与IPC/Q012-Looper-队列空闲时为什么不会一直占用-CPU.md)、[Q077](../questions/11-性能与稳定性/Q077-ANR-常见成因与排查流程是什么.md) | — |
| U11-16 | 源码学习方法 | 新题深化 | [source-ai](interview-intake-java-systems-20261102.md#js16) | — |
| U11-17 | AIDL步骤与Binder | 既有导航 | [WC33](word-crush-android-xml-guide.md#q33)、[Q015](../questions/02-Handler线程与IPC/Q015-Binder-如何完成一次跨进程调用.md) | — |
| U11-18 | 后台不被杀 | 既有导航 | [Q007](../questions/01-Android基础与生命周期/Q007-Activity-和-Service-有什么区别.md)、[PL18](android-platform-interview-guide.md#ad18)、[PL19](android-platform-interview-guide.md#ad19) | 无法给保活保证 |
| U11-19 | View绘制 | 既有导航 | [Q017](../questions/03-View绘制与触摸/Q017-View-的-measure、layout、draw-分别做什么.md) | — |
| U11-20 | 事件分发 | 既有导航 | [Q019](../questions/03-View绘制与触摸/Q019-触摸事件分发与拦截的职责如何划分.md) | — |
| U11-21 | 触摸拦截 | 既有导航 | [Q020](../questions/03-View绘制与触摸/Q020-父容器中途拦截手势时子-View-会发生什么.md)、[PL15](android-platform-interview-guide.md#ad15) | — |
| U11-22 | 新闻App功能设计 | 既有导航 | [PREP](interview-intake-coverage-20261102.md#准备框架)、[HC02](android-interview-handbook.md#q-c02)、[HC24](android-interview-handbook.md#q-c24) | 只按数据流/分页缓存/失败恢复设计，不编原项目 |
| U11-23 | MVP重构动机 | 扩充已有 | [Q066](../questions/10-Jetpack架构与存储/Q066-MVC、MVP、MVVM-如何划分职责.md) | — |
| U11-24 | MVP与MVVM | 扩充已有 | [Q066](../questions/10-Jetpack架构与存储/Q066-MVC、MVP、MVVM-如何划分职责.md) | — |
| U11-25 | 反问业务栈与跨端 | 新题深化 | [PREP](interview-intake-coverage-20261102.md#准备框架)、[render-platforms](interview-intake-network-runtime-20261102.md#nt01) | — |

## U12 小鹏 Android 一面截图

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U12-01 | 存储选择与Provider边界 | 扩充已有 | [Q070](../questions/10-Jetpack架构与存储/Q070-SharedPreferences、数据库各适合什么数据.md) | — |
| U12-02 | 单例、工厂、适配器 | 新题深化 | [dcl](interview-intake-java-systems-20261102.md#js02)、[patterns](interview-intake-java-systems-20261102.md#js04) | — |
| U12-03 | String、Builder、Buffer | 既有导航 | [JA04](java-core-interview-guide.md#ja04)、[Q043](../questions/07-Java集合与JVM/Q043-String-常量池与对象创建有什么区别.md) | — |
| U12-04 | ArrayList与LinkedList | 扩充已有 | [Q037](../questions/07-Java集合与JVM/Q037-ArrayList-为什么查询快而中间插入可能昂贵.md)、[JA08](java-core-interview-guide.md#ja08) | — |
| U12-05 | 四组件 | 扩充已有 | [Q001](../questions/01-Android基础与生命周期/Q001-四大组件各自解决什么问题.md) | — |
| U12-06 | 广播注册 | 既有导航 | [broadcast](../questions/01-Android基础与生命周期/Q001-四大组件各自解决什么问题.md) | — |
| U12-07 | 启动Service | 既有导航 | [Q007](../questions/01-Android基础与生命周期/Q007-Activity-和-Service-有什么区别.md)、[WC32](word-crush-android-xml-guide.md#q32) | — |
| U12-08 | A到B到A生命周期 | 既有导航 | [Q002](../questions/01-Android基础与生命周期/Q002-Activity-切换与返回时的生命周期如何变化.md) | — |
| U12-09 | 源码和开源库阅读 | 新题深化 | [source-ai](interview-intake-java-systems-20261102.md#js16) | — |
| U12-10 | TCP服务端感知断开 | 新题深化 | [disconnect](interview-intake-network-runtime-20261102.md#nt09) | — |
| U12-11 | Binder载荷限制 | 扩充已有 | [Q016](../questions/02-Handler线程与IPC/Q016-为什么大数据不应直接塞进-Binder-事务.md)、[PL13](android-platform-interview-guide.md#ad13) | — |
| U12-12 | 通话、日历提醒和音乐铃声互斥 | 新题深化 | [audio-focus](interview-intake-android-20261102.md#ad12) | — |
| U12-13 | 进程与线程 | 既有导航 | [Q081](../questions/12-Framework与系统/Q081-进程和线程的资源边界有什么不同.md) | — |
| U12-14 | Linux CPU与内存命令 | 新题深化 | [linux-metrics](interview-intake-java-systems-20261102.md#js09) | — |
| U12-15 | 系统启动与插充电流程 | 新题深化 | [startup-charging](interview-intake-android-20261102.md#ad13) | 原话为插充电一瞬间，按开机/关机充电/已开机区分 |
| U12-16 | Glide | 新题深化 | [glide](interview-intake-android-20261102.md#ad11) | — |
| U12-17 | 冷启动 | 既有导航 | [Q078](../questions/11-性能与稳定性/Q078-应用启动优化怎样区分首帧与可交互时间.md)、[PL32](android-platform-interview-guide.md#ad32) | — |
| U12-18 | GC | 既有导航 | [Q040](../questions/07-Java集合与JVM/Q040-垃圾回收怎样判断对象是否仍然存活.md)、[JA37](java-core-interview-guide.md#ja37) | — |
| U12-19 | 两根木棍测45分钟 | 新题深化 | [burn-ropes](interview-intake-algorithms-20261102.md#al08) | — |

## U13 未标公司 Flutter/Android 连续三页截图

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U13-01 | 自介与Android掌握程度 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |
| U13-02 | Dart GC | 新题深化 | [dart-gc](interview-intake-network-runtime-20261102.md#nt15) | 不采用原帖口述算法数量作为事实 |
| U13-03 | const与final | 既有导航 | [FL01](flutter-interview-guide.md#q01) | — |
| U13-04 | Widget、Element、RenderObject | 既有导航 | [FL15](flutter-interview-guide.md#q15) | 原图Wind Object疑术语笔误，规范化说明 |
| U13-05 | build范围、markNeedsBuild与BuildOwner | 既有导航 | [FL16](flutter-interview-guide.md#q16)、[FL22](flutter-interview-guide.md#q22) | — |
| U13-06 | StatefulWidget生命周期与网络清理 | 既有导航 | [FL19](flutter-interview-guide.md#q19)、[FL21](flutter-interview-guide.md#q21)、[FL23](flutter-interview-guide.md#q23) | — |
| U13-07 | 原生通信 | 既有导航 | [FL40](flutter-interview-guide.md#q40) | — |
| U13-08 | 网络插件与路由库选择 | 新题深化 | [hybrid-routing](interview-intake-network-runtime-20261102.md#nt16) | 原文未知库名，不能猜所谓美团路由实现 |
| U13-09 | 路由的平台差异 | 新题深化 | [hybrid-routing](interview-intake-network-runtime-20261102.md#nt16)、[FL35](flutter-interview-guide.md#q35) | — |
| U13-10 | Handler组成 | 既有导航 | [Q009](../questions/02-Handler线程与IPC/Q009-Handler、Looper-和-MessageQueue-如何协作.md) | — |
| U13-11 | 主Looper未建情况及机制 | 扩充已有 | [Q014](../questions/02-Handler线程与IPC/Q014-HandlerThread-与普通-Thread-有何差别.md) | 实际主Looper由系统创建，不建议应用prepareMainLooper |
| U13-12 | 四组件 | 扩充已有 | [Q001](../questions/01-Android基础与生命周期/Q001-四大组件各自解决什么问题.md) | — |
| U13-13 | 启动模式 | 既有导航 | [Q003](../questions/01-Android基础与生命周期/Q003-Activity-启动模式与-onNewIntent-如何配合.md) | — |
| U13-14 | Java四引用 | 既有导航 | [Q041](../questions/07-Java集合与JVM/Q041-强引用、软引用、弱引用和虚引用如何使用.md)、[JA36](java-core-interview-guide.md#ja36) | — |
| U13-15 | 线程池作用 | 扩充已有 | [Q051](../questions/08-并发与线程安全/Q051-线程池参数怎样共同决定任务执行.md) | — |
| U13-16 | 挑战案例 | 新题深化 | [PREP](interview-intake-coverage-20261102.md#准备框架)、[source-ai](interview-intake-java-systems-20261102.md#js16) | — |
| U13-17 | 学习方法与AI | 新题深化 | [source-ai](interview-intake-java-systems-20261102.md#js16) | — |
| U13-18 | AI工具 | 新题深化 | [source-ai](interview-intake-java-systems-20261102.md#js16)、[FL52](flutter-interview-guide.md#q52) | — |
| U13-19 | 新Flutter与老Java迁移 | 新题深化 | [render-platforms](interview-intake-network-runtime-20261102.md#nt01) | 工程取舍观点，不当成某公司固定路线 |
| U13-20 | 移动端前景 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | 观点型问题，不写确定行业预测 |

## U14 未标公司客户端面经重复截图

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U14-01 | iOS了解程度 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | 按真实边界回答，不补iOS项目经历 |
| U14-02 | 四组件 | 扩充已有 | [Q001](../questions/01-Android基础与生命周期/Q001-四大组件各自解决什么问题.md) | — |
| U14-03 | Activity生命周期 | 既有导航 | [Q002](../questions/01-Android基础与生命周期/Q002-Activity-切换与返回时的生命周期如何变化.md)、[Q006](../questions/01-Android基础与生命周期/Q006-如何判断应用处于前台还是后台.md) | — |
| U14-04 | Activity A跳B | 既有导航 | [Q002](../questions/01-Android基础与生命周期/Q002-Activity-切换与返回时的生命周期如何变化.md) | — |
| U14-05 | 图片缓存 | 新题深化 | [glide](interview-intake-android-20261102.md#ad11) | — |
| U14-06 | LRU | 既有导航 | [Q108](../questions/15-数据结构与算法/Q108-怎样设计-LRU-缓存.md) | — |
| U14-07 | 实习节假日三级数据源 | 待澄清 | [ASK](interview-intake-coverage-20261102.md#待澄清清单) | 不知原项目哪三级，不能编内存磁盘网络当原答 |
| U14-08 | RN页面改H5原因 | 新题深化 | [h5-bridge](interview-intake-network-runtime-20261102.md#nt14) | — |
| U14-09 | RN热更新后为何仍选H5 | 新题深化 | [h5-bridge](interview-intake-network-runtime-20261102.md#nt14) | — |
| U14-10 | JSBridge新增接口 | 新题深化 | [h5-bridge](interview-intake-network-runtime-20261102.md#nt14) | — |
| U14-11 | 老版本接口适配 | 新题深化 | [h5-bridge](interview-intake-network-runtime-20261102.md#nt14)、[Q116](../questions/16-工程设计与项目追问/Q116-多机型兼容问题应怎样建立验证矩阵.md) | — |
| U14-12 | RecyclerView复用 | 既有导航 | [Q023](../questions/04-RecyclerView/Q023-RecyclerView-所谓四级缓存究竟是什么.md)、[Q024](../questions/04-RecyclerView/Q024-从缓存或回收池取出的-ViewHolder-是否都要重新绑定.md) | — |
| U14-13 | Activity外内存泄漏 | 既有导航 | [Q074](../questions/11-性能与稳定性/Q074-内存泄漏与-OOM-是什么关系.md)、[JA31](java-core-interview-guide.md#ja31)、[JA38](java-core-interview-guide.md#ja38) | — |
| U14-14 | 第n大与复杂度 | 新题深化 | [smallest-k](interview-intake-algorithms-20261102.md#al03) | — |

## U15 小米高级Android服务账号整理图

| 议题ID | 归纳议题 | 处理 | 答案或准备入口 | 边界/缺失说明 |
|---|---|---|---|---|
| U15-01 | Activity后台生命周期 | 既有导航 | [Q002](../questions/01-Android基础与生命周期/Q002-Activity-切换与返回时的生命周期如何变化.md)、[Q006](../questions/01-Android基础与生命周期/Q006-如何判断应用处于前台还是后台.md) | — |
| U15-02 | Service启动绑定与机器人前台服务 | 既有导航 | [Q007](../questions/01-Android基础与生命周期/Q007-Activity-和-Service-有什么区别.md)、[WC32](word-crush-android-xml-guide.md#q32)、[PL20](android-platform-interview-guide.md#ad20) | — |
| U15-03 | 多进程IPC取舍 | 既有导航 | [Q015](../questions/02-Handler线程与IPC/Q015-Binder-如何完成一次跨进程调用.md)、[PL11](android-platform-interview-guide.md#ad11)、[PL12](android-platform-interview-guide.md#ad12) | — |
| U15-04 | Handler高频传感器阻塞 | 新题深化 | [sensor-pipeline](interview-intake-android-20261102.md#ad14) | — |
| U15-05 | View卡顿 | 既有导航 | [Q076](../questions/11-性能与稳定性/Q076-列表滚动掉帧应怎样定位.md)、[PL33](android-platform-interview-guide.md#ad33) | — |
| U15-06 | 权限与机器人硬件适配 | 新题深化 | [device-engineering](interview-intake-android-20261102.md#ad14)、[PL36](android-platform-interview-guide.md#ad36) | — |
| U15-07 | 多屏适配 | 新题深化 | [adaptive-grid](interview-intake-android-20261102.md#ad04)、[device-engineering](interview-intake-android-20261102.md#ad14) | — |
| U15-08 | 高频上传防抖与背压 | 新题深化 | [sensor-pipeline](interview-intake-android-20261102.md#ad14)、[KT35](kotlin-coroutines-interview-guide.md#kt35) | — |
| U15-09 | 常驻对象泄漏 | 新题深化 | [device-engineering](interview-intake-android-20261102.md#ad14)、[JA38](java-core-interview-guide.md#ja38) | — |
| U15-10 | 大量传感器持久化 | 新题深化 | [sensor-pipeline](interview-intake-android-20261102.md#ad14) | — |
| U15-11 | JNI驱动接口 | 新题深化 | [device-engineering](interview-intake-android-20261102.md#ad14)、[JA39](java-core-interview-guide.md#ja39) | — |
| U15-12 | 长期日志容量 | 新题深化 | [device-engineering](interview-intake-android-20261102.md#ad14) | — |
| U15-13 | 冷启动 | 既有导航 | [Q078](../questions/11-性能与稳定性/Q078-应用启动优化怎样区分首帧与可交互时间.md)、[PL32](android-platform-interview-guide.md#ad32) | — |
| U15-14 | Jetpack与ViewModel | 扩充已有 | [Q068](../questions/10-Jetpack架构与存储/Q068-ViewModel-为什么能跨配置变化保留状态.md)、[PL01](android-platform-interview-guide.md#ad01) | — |
| U15-15 | 协程与线程 | 既有导航 | [Q032](../questions/06-Kotlin与协程/Q032-协程和线程是什么关系.md)、[KT18](kotlin-coroutines-interview-guide.md#kt18) | — |
| U15-16 | 后台查杀和保活 | 既有导航 | [Q007](../questions/01-Android基础与生命周期/Q007-Activity-和-Service-有什么区别.md)、[PL19](android-platform-interview-guide.md#ad19) | — |
| U15-17 | 线上ANR | 既有导航 | [Q077](../questions/11-性能与稳定性/Q077-ANR-常见成因与排查流程是什么.md)、[PL31](android-platform-interview-guide.md#ad31) | — |
| U15-18 | 指令队列顺序 | 新题深化 | [sensor-pipeline](interview-intake-android-20261102.md#ad14) | 区分投递、执行、完成和重试，不承诺exactly-once |
| U15-19 | 实时预览图像内存 | 既有导航 | [Q079](../questions/11-性能与稳定性/Q079-Bitmap-的内存占用怎样估算.md)、[PL34](android-platform-interview-guide.md#ad34) | — |
| U15-20 | 版本碎片化 | 既有导航 | [Q116](../questions/16-工程设计与项目追问/Q116-多机型兼容问题应怎样建立验证矩阵.md)、[JA40](java-core-interview-guide.md#ja40) | — |
| U15-21 | 受限设备轻量化 | 新题深化 | [Q080](../questions/11-性能与稳定性/Q080-怎样减少-APK-体积且避免破坏运行时行为.md)、[device-engineering](interview-intake-android-20261102.md#ad14) | — |
| U15-22 | 反问 | 准备框架 | [PREP](interview-intake-coverage-20261102.md#准备框架) | — |

## 校验与实际限制

结构化题库已重新生成并检查数据、归属和本地链接；本批清单另检查252条议题目标文件与锚点、新题全部有映射、未知日期隔离。浏览器与服务端的实际解析器读取548个一致题目ID，原491个ID完整保留。

算法在2026-11-02使用临时Temurin JDK 21.0.13+9编译，Python两项检查通过，Java输出 `PASS: 61162 algorithm checks`；代码与Markdown示例一致，包含随机/枚举对照和长链边界。四专题及既有答案增量经过独立静态技术复核。

这不是Android APK构建、真机、抓包、音频/代理/硬件测试或线上性能测量，也未对原面试发生事实认证。官方页面与主分支源码会变，不能把OpenJDK细节无条件套到所有Android版本；少数官方入口访问失败已在对应题注明。

复查命令（仓库根目录）：

```bash
python3 scripts/build.py --check
python3 scripts/validate.py
python3 scripts/build_intake_report.py --check
python3 -m unittest discover -s tests -p 'test_repository.py' -v
python3 -m unittest discover -s tests -p 'test_interview_algorithms.py' -v
```

网站按现有服务器缓存读取GitHub更新；手动点“更新题库”即可请求更新。本次资料更新不要求重新部署，不更改服务器或其他在线服务。

机器可读清单：[20261102.json](../data/intakes/20261102.json)；维护题号与路径，避免破坏收藏和学习进度。
