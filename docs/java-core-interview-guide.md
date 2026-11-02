# Java 与 ART：Android 实习面试的 40 个深入问答

核对日期：2026-11-01。本文包含 **40 道整理者设计的通用练习题**：基础必会 JA01—JA25，进阶追问 JA26—JA40。它们不属于某家公司的已证实面试记录，不表达招聘频率，也不证明任何个人参与过对应改造、定位过故障或已经掌握这些能力。P0/P1 只是学习顺序建议。

**证据与版本边界：** Java 语言语义参考所链接的 JLS；Java SE 17/21 API 文档只证明对应版本的契约，不能直接证明 Android 的方法可用性或内部实现相同。JVMS 的抽象运行时规则、HotSpot 的实现细节与 Android ART 必须区分；设备结论还要核对 Android API、AGP、脱糖配置和具体系统版本。本文未编译示例、未执行并发实验、未运行真机、未做性能或安全测量；示例是解释机制的短片段，不是生产实现或测试通过证明。

每题先用“口述回答”讲 30—60 秒，再解释一个失效场景和验证方法。文中 Android 场景均为练习设定，不能改写成个人项目事实；真实项目实现仍以已有指南固定的源码版本为准。

已有 [Java 集合与 JVM 题库](../questions/07-Java集合与JVM/README.md) 和 [并发题库](../questions/08-并发与线程安全/README.md) 负责概念入口；本篇补足 API 契约、对象别名、并发复合操作与 Android 版本边界，避免只背定义。

| 已有入口 | 本篇深入角度 |
| --- | --- |
| Q034/Q035/Q037/Q042，手册 C11/C43 | JA01—JA10、JA26：键稳定性、排序等价关系、视图与快照、迭代协议 |
| Q038，手册 C45，Flutter Q04 | JA11—JA13：API 的读写约束、类型证据、桥接方法与堆污染 |
| Q047—Q055，手册 C43 | JA16—JA22、JA27—JA34：发布证明、业务不变量、过载、终止与可观察错误 |
| Q039—Q041，手册 C42/C46 | JA23—JA25、JA35—JA40：运行时与类身份、引用链、ART/GC/JNI 和兼容性 |
| [Word Crush XML 指南 Q24—Q28](word-crush-android-xml-guide.md#q24) | JA21/JA22/JA32/JA33：线程池、Future 与回调只是通用深化，不声称旧项目已采用新方案 |
| [FeedLine 指南](feedline-android-deep-dive.md)、[Flutter 指南](flutter-interview-guide.md) | Java 内存模型与 Dart Isolate、Kotlin 协程应按各自模型比较，不能互相替代证明 |
| [Rust SDK 导读](sdk-source-deep-dive.md)、[QUIC 导读](quic-source-deep-dive.md)、[AI 接管练习册](ai-code-takeover-workbook.md) | JA32/JA39 的取消与所有权是对照练习，不把 JNI 当作现有 Flutter C ABI 实现 |

## 基础必会（JA01–JA25）

<a id="ja01"></a>
### JA01 P0 业务对象作为 Map 的 key 时怎样设计相等性

**口述回答：** 先定义业务上什么叫同一个键，再保证 `equals` 的对称、传递、一致及与 `hashCode` 的配合。哈希键参与相等性判断的字段入表后应保持稳定；昵称等可变展示字段通常不适合当身份。两个不同对象可以表示同一业务 ID，两个内容相近对象也未必属于同一实体。

**原理与边界：** 修改键的相关字段后，容器行为不再有可靠契约，不能依赖“遍历还在就一定能 get”。继承体系额外加入相等字段容易破坏对称性；组合或明确的值类型边界通常更容易推理。这里比 [Q034](../questions/07-Java集合与JVM/Q034-Java-的-equals、hashCode-与双等号如何区分.md) 更关注模型设计。

**追问：** 键信息必须改变怎么办？ **答：** 在旧键仍稳定时移除映射，再以新键重新插入；更常见的是保留稳定 ID，把变化内容放在 value 中。

**常见误区：** `hashCode` 不是全局唯一 ID，不能用于持久标识，也不能只重写 `equals`。

**官方依据：** [Object 的 equals/hashCode 契约](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Object.html#equals(java.lang.Object))；[Map 对可变 key 的限制](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Map.html)。

<a id="ja02"></a>
### JA02 P0 TreeSet 为什么可能把两个不同对象当成同一项

**口述回答：** 有序集合按比较结果判断排序位置与键等价关系；比较器返回零的两个元素会被视为相同排序键。因此仅按年龄排序的 TreeSet 可能合并两个同龄用户。需要集合去重含义与业务身份一致时，应让比较器的零结果和 `equals` 一致，或另用列表排序、Map 去重。

**原理与边界：** 比较器必须满足符号反向和传递等要求。用 `a.score - b.score` 可能整数溢出，宜用 `Integer.compare`，必要时增加稳定 ID 作为后续排序键。排序稳定性不等于集合会保留所有同分对象。

**追问：** 增加 ID 比较一定正确吗？ **答：** 只有业务确实按 ID 区分元素时才正确；若 equals 包含其他字段，还需重新检查两套等价关系。

**常见误区：** 以为所有 Set 都依据 hashCode 去重，或比较器只影响显示顺序。

**官方依据：** [Comparator 的一致性与顺序契约](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Comparator.html)。

<a id="ja03"></a>
### JA03 P0 装箱拆箱为何会让集合删除和空值判断出错

**口述回答：** 基本类型和包装类型有自动转换，但 null 包装值不能拆箱，包装对象之间的 `==` 也不能当通用数值比较。重载还会改变含义：`List<Integer>` 的 `remove(1)` 删除索引 1，`remove(Integer.valueOf(1))` 删除值为 1 的首个元素。先看静态参数类型，再判断执行哪个签名。

**原理与边界：** 包装对象可能复用，不能依赖某次引用比较结果推导所有数值、构造方式和运行时都相同。`Integer x = null; if (x == 0)` 会在比较前拆箱。频繁装箱的分配和性能影响应测量，不能仅从源码给出固定对象数量。

**追问：** 怎么安全比较两个可空 Integer？ **答：** 可用 `Objects.equals(a, b)` 表达两者相等或同时为 null；若业务不允许 null，则先校验而不是静默用零代替。

**常见误区：** “用了泛型就不会出现运行时 NPE”，或所有 `remove` 都按值删除。

**官方依据：** [JLS 5.1.7/5.1.8 装箱与拆箱](https://docs.oracle.com/javase/specs/jls/se17/html/jls-5.html#jls-5.1.8)；[List 的两个 remove 重载](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/List.html)。

<a id="ja04"></a>
### JA04 P0 循环拼接日志为什么不能只背 StringBuilder 更快

**口述回答：** 如果每次循环都把旧字符串和新片段组合，结果增长时可能反复复制已有内容；显式复用一个局部 StringBuilder 可以表达逐步构建，再一次转为 String。但编译器和运行时可能优化普通拼接，真实收益取决于循环规模、是否需要结果和实际编译链路。

**原理与边界：** StringBuilder 可变且不保证多线程安全，适合作为局部构建器。放进全局缓存会引入并发与大容量长期保留问题。字符串常量池回答见 [Q043](../questions/07-Java集合与JVM/Q043-String-常量池与对象创建有什么区别.md)，这里关注数据量和对象生命周期。

**追问：** 改成 StringBuffer 就能保证整段日志不交错吗？ **答：** 其单方法同步不自动保证多个 append 组成的业务操作整体互斥，还要确定共享范围。

**常见误区：** 承诺所有 `+` 都创建固定数量对象，或为了“复用”让 Activity 永久持有大构建器。

**官方依据：** [StringBuilder 的可变性、容量和同步边界](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/StringBuilder.html)。

<a id="ja05"></a>
### JA05 P0 把 List 复制后交给 UI 为什么仍可能被后台改坏

**口述回答：** `new ArrayList<>(source)` 复制列表结构，元素引用仍共享。后台修改某个 User 对象，UI 的列表也能看到该对象变化；这不是深拷贝。需要稳定 UI 快照时，要确定元素及嵌套字段的不可变范围，必要时转换为独立的展示模型，再通过安全线程边界发布。

**原理与边界：** 拷贝时源集合若被无同步地并发修改，也不能保证拿到一致快照。深拷贝更不是把文件句柄、线程、数据库连接递归复制一遍；资源共享要有明确所有权。这是在 [Q044](../questions/07-Java集合与JVM/Q044-深拷贝与浅拷贝有什么区别.md) 之上推导真实异步交付问题。

**追问：** 复制后包装成不可修改 List 足够吗？ **答：** 只能限制通过这个包装器修改列表结构，不能冻结共享元素，更不能替代发布与同步。

**常见误区：** 把“不同 List 实例”当成“完全独立的对象图”。

**官方依据：** [ArrayList 的集合复制构造](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ArrayList.html#%3Cinit%3E(java.util.Collection))；[Collections 的不可修改视图](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List))。

<a id="ja06"></a>
### JA06 P0 fixed-size、unmodifiable view 和不可变快照有什么差别

**口述回答：** `Arrays.asList(array)` 是数组的定长视图，允许替换元素但不能增删，数组变化也能反映到列表；`Collections.unmodifiableList(list)` 限制通过包装器修改，但底层 list 仍可能被其他引用修改。真正需要独立结构快照时，应先复制；元素是否可变另行讨论。

**原理与边界：** Java SE 的 `List.copyOf` 提供不反映后续源集合结构变化的不可修改列表，但不深拷贝元素，且不接收 null。该方法的 Android 可用性仍需按 JA40 检查，不能照搬桌面 JDK 示例。

**追问：** 把 `int[]` 传给 `Arrays.asList` 会得到很多 Integer 吗？ **答：** 不会自动逐项装箱，推导出的列表包含一个 `int[]` 元素；需要显式转换。

**常见误区：** 把不可修改包装称为完全不可变，或遇到 UnsupportedOperationException 就认为 API 出了故障。

**官方依据：** [Arrays.asList](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Arrays.html#asList(T...))；[List.copyOf](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/List.html#copyOf(java.util.Collection))。

<a id="ja07"></a>
### JA07 P0 subList 用于分页时有哪些别名和生命周期风险

**口述回答：** `subList` 通常用于表示原列表某一段的视图，区间内的修改可能反映到底层；它不是分页数据的独立副本。若后续通过其他路径结构性修改原列表，视图语义会失效。要跨异步边界或长期缓存一页，通常先复制出所需元素，并继续考虑元素共享。

**原理与边界：** List 契约明确规定了视图与底层列表的关系；具体实现还可能因持有底层结构而延长大列表或相关元素的生命，应以目标实现和堆引用链核实，不能把某种内存布局当全部实现的保证。

**追问：** `subList(...).clear()` 能用来删除原列表区间吗？ **答：** 在支持相应修改的列表上可以，这正利用了视图语义；需要外部同步时也要保持同一锁协议。

**常见误区：** 认为视图只会复制区间内的数据，或认为捕获异常后继续使用失效视图可靠。

**官方依据：** [List.subList 的背靠列表与失效规则](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/List.html#subList(int,int))。

<a id="ja08"></a>
### JA08 P0 为什么把 ArrayList 换成 LinkedList 可能让遍历更慢

**口述回答：** 不能只看“链表插入快”。对 LinkedList 不断调用 `get(i)`，每次可能需要从头或尾走到对应节点，整个下标循环可能退化成平方级工作。ArrayList 随机访问更合适；需要顺序处理链表时用迭代器，是否换容器要结合定位成本、分配和访问模式。

**原理与边界：** 链表已定位节点附近的修改与“先按索引找到节点再修改”不是同一个成本。实际 Android 表现还受数据规模和设备影响，不能只用复杂度宣称必然提速。复杂度入口见 [Q037](../questions/07-Java集合与JVM/Q037-ArrayList-为什么查询快而中间插入可能昂贵.md)。

**追问：** 只做队首队尾操作怎么办？ **答：** 先看 Deque 接口及适合实现，不要为了双端操作强行使用 List 下标 API；再按 null、并发和容量需求选择。

**常见误区：** 把“插入节点 O(1)”省略成“任意索引插入整体 O(1)”。

**官方依据：** [LinkedList 的索引遍历说明](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/LinkedList.html)。

<a id="ja09"></a>
### JA09 P0 Map.get 返回 null 时究竟能断定什么

**口述回答：** 对允许 null value 的 Map，get 为 null 可能是没这个键，也可能是显式映射到 null，单看结果不能区分。可以按需求使用 containsKey，或禁止把 null 当有效业务值。并发容器的空值规则可能不同，不能把 HashMap 的用法直接复制过去。

**原理与边界：** `getOrDefault` 不是“结果为 null 就回退”；存在到 null 的映射时仍可返回 null。默认 `computeIfAbsent` 对缺失或 null 映射尝试计算，函数返回 null 时不建立非空映射；普通 Map 的这些默认方法不自动提供并发原子性。

**追问：** 在 HashMap 中先 containsKey 再 get 能解决并发吗？ **答：** 不能，两步之间仍可能发生变化；要明确线程封闭、统一加锁或并发原子操作协议。

**常见误区：** 把 null 同时表示“正在加载”“加载失败”和“不存在”，让调用者无法区分状态。

**官方依据：** [Map.get/getOrDefault/computeIfAbsent 契约](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Map.html#computeIfAbsent(K,java.util.function.Function))。

<a id="ja10"></a>
### JA10 P0 没抛 ConcurrentModificationException 就说明遍历安全吗

**口述回答：** 不能。ArrayList 等迭代器的 fail-fast 是尽力发现错误的机制，不是并发正确性保证。单线程在增强 for 中直接通过列表结构修改也可能违反迭代协议；需要边遍历边删时可使用受支持的 Iterator.remove，或先收集再统一修改。

**原理与边界：** 多线程情况下应先选同步、线程封闭或满足需求的并发容器。某次没有抛异常不证明读到一致快照；某些并发容器本来就采用弱一致或快照迭代器，也不能用是否抛异常区分线程安全。

**追问：** 给迭代器代码加 try/catch 然后重试靠谱吗？ **答：** 不能作为一致性方案；可能重复副作用或一直冲突，仍需定义要观察哪个版本的数据。

**常见误区：** 将 fail-fast 当锁，或用一次运行结果证明没有竞争。

**官方依据：** [ArrayList 关于 fail-fast 的尽力保证](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ArrayList.html)。

<a id="ja11"></a>
### JA11 P0 如何用 PECS 设计可复用的集合复制接口

**口述回答：** 方法从来源读取 T 时，来源可写成 `? extends T`；向目标写入 T 时，目标可写成 `? super T`。例如 `copy(List<? extends T> src, List<? super T> dst)` 表达来源生产、目标消费。若同一参数既要按 T 读又要按 T 写，通常需要明确的 T，而不是盲目加通配符。

**原理与边界：** 从 `? extends Number` 可以读成 Number，却不能安全插入任意 Integer，因为实际元素类型可能是 Double。它不是严格不可变容器，仍可能支持 clear 等操作。与 [手册 C45](android-interview-handbook.md#q-c45) 对照 Java 使用点通配符和 Kotlin 声明点型变。

**追问：** 从 `? super Integer` 读出什么类型？ **答：** 通常只能安全视为 Object；下界保证能接收 Integer，不保证里面只有 Integer。

**常见误区：** 把 extends 简化为“只读且线程安全”，忽略容器操作和对象可变性。

**官方依据：** [Oracle 通配符使用指南](https://docs.oracle.com/javase/tutorial/java/generics/wildcardGuidelines.html)。

<a id="ja12"></a>
### JA12 P0 为什么反序列化需要 Type 而一个 List.class 不够

**口述回答：** `List.class` 只能描述原始列表类，不能单独描述 `List<User>` 的元素结构。类型擦除使普通对象实例不天然携带完整泛型实参；某些库利用声明中的泛型签名捕获 Type。应沿实际声明验证捕获了什么，不能把“用了匿名子类”当作一定保留所有类型参数。

**原理与边界：** 在泛型方法内部捕获 `List<T>`，得到的 T 仍可能是未解析的类型变量；这和直接声明具体 User 不同。类型元数据也不验证网络数据内容；缺字段、非法值和多态边界仍需校验。原始概念见 [Q038](../questions/07-Java集合与JVM/Q038-Java-泛型擦除后还能获得哪些类型信息.md)。

**追问：** `instanceof List<?>` 能检查所有元素是 User 吗？ **答：** 不能，它只检查可具体化的列表形态；元素需另行验证或由可信解析过程建立约束。

**常见误区：** 以为擦除后完全没有声明元数据，或反过来以为任意对象都能恢复 List<User>。

**官方依据：** [JLS 4.6/4.7 类型擦除与可具体化类型](https://docs.oracle.com/javase/specs/jls/se17/html/jls-4.html#jls-4.6)。

<a id="ja13"></a>
### JA13 P1 为什么错误写入泛型集合后会到读取时才报错

**口述回答：** raw type 或未检查转换可能绕过编译期泛型约束，把不符合声明类型的值塞进集合，形成堆污染。读取时编译器插入的类型转换才触发 ClassCastException。消除 unchecked 警告要证明边界，而不是统一加 SuppressWarnings。

**原理与边界：** 泛型数组和可变参数需要特别谨慎：不可具体化元素类型与数组别名可能破坏约束。继承泛型类时，编译器还可能生成桥接方法维持擦除后的重写关系，所以异常栈里可能出现源码没写的转发方法。

**追问：** 为什么不能因参数是 `List<String>...` 就随意写入它的数组？ **答：** 数组可能通过更宽类型产生别名，写入其他参数化类型后污染；SafeVarargs 是程序员对安全用法的承诺，不是自动修复。

**常见误区：** 将桥接方法当业务重复调用，或认为所有泛型运行时错误都在插入位置立即发生。

**官方依据：** [JLS 4.12.2 堆污染](https://docs.oracle.com/javase/specs/jls/se17/html/jls-4.html#jls-4.12.2)；[Oracle 桥接方法说明](https://docs.oracle.com/javase/tutorial/java/generics/bridgeMethods.html)。

<a id="ja14"></a>
### JA14 P0 异常转换时怎样保留可诊断信息而不假报成功

**口述回答：** 先区分调用者能处理的失败、程序错误与严重运行时问题，再选择抛出、转换或明确的失败结果。转换异常时保留 cause 及必要上下文，不能只留 `getMessage()`。checked 与 unchecked 主要影响编译期处理要求，不等于“可恢复”和“绝对不可恢复”的机械分类。

**原理与边界：** `catch (Exception)` 不包括 Error；`catch (Throwable)` 会把更广的严重错误也捕获，不能当“保证程序不崩”的常规方案。资源状态、取消信号和已完成的外部副作用都要单独处理。与 [FeedLine 的异常边界](feedline-android-deep-dive.md) 对照：吞掉异常不应让 UI 将缓存回退显示成远端成功。

**追问：** 记录日志后返回空列表可以吗？ **答：** 只有业务契约明确接受“失败等价于空数据”才可这样设计；否则需要区分 Empty 与 Failed，避免误删已有 UI 数据。

**常见误区：** 捕获一切后继续使用半初始化对象，或同一异常层层重复记录却丢失原始 cause。

**官方依据：** [JLS 第 11 章异常分类与传播](https://docs.oracle.com/javase/specs/jls/se17/html/jls-11.html)。

<a id="ja15"></a>
### JA15 P0 try-with-resources 遇到业务异常和关闭异常会留下谁

**口述回答：** 多个资源按声明的反向顺序关闭。若主体先抛异常，关闭时的异常通常作为 suppressed 异常附在原异常上，避免覆盖主要失败；若主体成功而关闭失败，关闭异常仍可能传播。因此“计算返回值了”不保证整个 try 已成功结束。

**原理与边界：** try-with-resources 表达 AutoCloseable 所有权，适合流等需要确定释放的资源，但不能关闭调用者仍拥有的共享资源。自己写 finally 时的 return 或新抛异常可能掩盖原失败，排障应同时查看 cause 与 suppressed。

**追问：** 第二个资源初始化失败，第一个会关闭吗？ **答：** 已成功初始化并进入资源管理范围的前面资源仍会按规则关闭；失败对象本身的构造清理则要由其实现保证。

**常见误区：** 认为 GC 会及时关闭文件，或认为所有“可关闭”对象都适合在主线程等待关闭；线程池另见 JA32。

**官方依据：** [Oracle try-with-resources 与 suppressed 异常](https://docs.oracle.com/javase/tutorial/essential/exceptions/tryResourceClose.html)。

<a id="ja16"></a>
### JA16 P0 怎样证明后台写入的数据对读取线程可见

**口述回答：** 要找具体的 happens-before 链，而不是说“它先执行了”。同一监视器的释放与后续获取、同一 volatile 的写与后续读，以及 start、成功 join 等有规定关系；再利用程序顺序和传递性连接到目标读写。仅靠日志时间、sleep 或一次复现结果不能证明安全发布。

**原理与边界：** happens-before 是语言规定的可见性和顺序约束，不是要求所有机器指令严格按现实时间排序。缺乏同步的竞争读写可能有多种合法表现；不能用“CPU 最终会刷新”代替正确协议。这是 [Q047](../questions/08-并发与线程安全/Q047-volatile-保证什么，为什么不能保证自增原子性.md) 的证明方法补充。

**追问：** 把对象交给 Executor 前的写入有何意义？ **答：** Executor 的内存一致性契约连接提交前动作与任务动作；后续再无同步修改同一对象仍可能竞争。

**常见误区：** 把“线程安全方法调用过一次”当后续所有字段访问都安全。

**官方依据：** [JLS 17.4.5 happens-before](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html#jls-17.4.5)；[Executor 的内存一致性](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Executor.html)。

<a id="ja17"></a>
### JA17 P0 volatile 引用发布配置时怎样避免混读两个版本

**口述回答：** 可以先完整构造不可变配置，再一次赋给 volatile 引用；读取方先取一次引用到局部变量，再从同一个配置对象读全部字段。这样既建立发布关系，也避免两次读取全局引用恰好跨越更新，得到地址来自旧版、端口来自新版的混合业务状态。

**原理与边界：** volatile 作用在引用读写上，不冻结对象内的 List、Map 或后续字段修改。若快照里仍有可变子对象，就必须复制、线程封闭或额外同步。多字段快照是设计选择，不能把它扩张成多对象事务。

**追问：** volatile List 的 add/remove 能同时执行吗？ **答：** 不能由引用 volatile 推出内部操作安全，仍需选择并发容器或统一锁；读取一次引用也不解决元素竞争。

**常见误区：** 把 volatile 描述为“每次刷新所有缓存”，或只给多个独立字段分别加 volatile 就声称得到整体一致版本。

**官方依据：** [JLS volatile 与同步顺序](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html#jls-17.4.4)。

<a id="ja18"></a>
### JA18 P0 两个线程安全计数器为什么维护不了一个业务不变量

**口述回答：** 每个 AtomicInteger 的操作原子，不代表“剩余数量加已分配数量等于总量”这类跨字段关系原子。先识别必须一起变化和一起观察的状态，再用同一锁保护整个操作，或以一个不可变状态整体进行原子替换。线程安全组件组合后仍要证明业务协议。

**原理与边界：** synchronized 既负责同一监视器互斥，也提供相应可见性；所有访问路径必须遵循相同锁。锁应稳定且不暴露给无关代码；耗时 I/O 和外部回调放在锁内还会带来等待与重入风险。

**追问：** 一部分读加锁，一部分只读 volatile 就行吗？ **答：** 除非能独立证明所需一致性，否则不能；读取多个有关字段也必须遵循一致快照协议。

**常见误区：** 以为方法名带 synchronized 就保护了所有对象，或锁住不同实例仍能互斥。

**官方依据：** [JLS 17.1 监视器](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html#jls-17.1)；[AtomicInteger 的单值原子语义](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/AtomicInteger.html)。

<a id="ja19"></a>
### JA19 P0 条件等待为什么必须先检查条件再循环 wait

**口述回答：** 条件本身才是继续执行的依据，通知不是可消费的业务结果。应在同一监视器内用 `while (!ready)` 检查并 wait；wait 释放该监视器，返回前重新获取，再检查条件。这样应对虚假唤醒，以及别的线程先拿走资源导致条件重新不成立。

**原理与边界：** wait 要持有相应对象监视器，只释放这个监视器，不会释放线程持有的所有锁。notify 不立即转交锁，多种条件共用等待集合时要认真选择 notifyAll 或分离条件。基础区别见 [Q049](../questions/08-并发与线程安全/Q049-sleep-与-wait-的区别是什么.md)。

**追问：** 先在锁外判断，再进锁直接 wait 可以吗？ **答：** 可能在两步之间错过状态变化与通知；条件检查和进入等待必须属于同一个受保护协议。

**常见误区：** 用 if 替代 while，或通知后不修改受保护状态，指望通知本身保存进度。

**官方依据：** [JLS 17.2.1 wait 的精确定义](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html#jls-17.2.1)。

<a id="ja20"></a>
### JA20 P0 正确处理中断为什么比捕获 InterruptedException 更重要

**口述回答：** 中断是协作取消信号，线程要在合适位置检查并停止工作；它不是强制终止。sleep、wait、join 等抛出 InterruptedException 时会清除中断状态，调用方若不能向上抛，通常应恢复标记并结束当前操作，而不是打印后继续无限循环。

**原理与边界：** 静态 `Thread.interrupted()` 检查当前线程并清除标记；实例 `isInterrupted()` 不清除。不同阻塞 API 对中断反应不同，CPU 循环和普通业务逻辑不会被神奇打断，文件或网络资源也要有自己的取消/关闭协议。

**追问：** 捕获后恢复标记然后立即重试同一个阻塞操作好吗？ **答：** 可能持续立即失败而空转；应按取消契约退出、向上传播或由明确边界消费信号。

**常见误区：** 把中断当异常噪声吞掉，或把 interrupt 返回当任务和资源已经停止的证明。

**官方依据：** [Thread 中断状态与 InterruptedException](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html#interrupt())。

<a id="ja21"></a>
### JA21 P0 核心线程数很小而最大线程数很大为何仍会排长队

**口述回答：** ThreadPoolExecutor 的通常接纳路径是先补到 core，再尝试入队，队列不能接纳时才尝试扩到 max，最后拒绝。无界队列通常一直能入队，因此 max 很少发挥扩容作用；任务可能越积越多，带来等待、内存和过期结果。不能只看最大线程数判断吞吐。

**原理与边界：** 有界队列把过载变成可观察事件，但还要设计拒绝、取消与调用方反馈。CallerRunsPolicy 可能让提交者执行任务，Android 主线程提交时可能因此阻塞；关闭后该策略会丢弃任务。不要未分析就作为通用“背压”。

**追问：** 提高 max 能解决所有排队吗？ **答：** 不能，先看队列策略是否允许扩容，再看任务是否受 I/O、锁或下游容量限制；盲目增加线程可能加重争用。

**常见误区：** 背成 core→max→queue，或把固定线程池的无界队列当作没有容量风险。

**官方依据：** [ThreadPoolExecutor 的排队、扩容与拒绝规则](https://developer.android.com/reference/java/util/concurrent/ThreadPoolExecutor)。

<a id="ja22"></a>
### JA22 P0 submit 的任务失败为什么可能看不到未捕获异常日志

**口述回答：** submit 通常把任务包装成 Future，任务异常保存在结果中，调用 get 时通过 ExecutionException 暴露；不能只依赖工作线程的未捕获异常处理器。execute 的未捕获 RuntimeException 传播路径与此不同。任务所有者要有统一的失败观察和报告位置，同时避免在主线程阻塞 get。

**原理与边界：** ThreadPoolExecutor.afterExecute 的 Throwable 对包装在 Future 中的失败可能为 null；如需检查结果，先判断对应 Future 已完成，再按取消、失败和成功分别处理。任务完成、结果被观察及 UI 成功展示是不同阶段。

**追问：** get 超时就说明任务失败了吗？ **答：** 只说明等待期限结束，任务可能仍执行；是否取消及怎样抑制迟到结果要另行设计，见 JA32。

**常见误区：** 提交成功就回报业务成功，或完全忽略 Future，导致任务失败变得不可观察。

**官方依据：** [ThreadPoolExecutor.afterExecute 的 Future 示例说明](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html#afterExecute(java.lang.Runnable,java.lang.Throwable))；[Future.get](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Future.html)。

<a id="ja23"></a>
### JA23 P0 没有泄漏为什么仍会频繁 GC 并出现卡顿

**口述回答：** 泄漏关注不该存活的对象仍被引用；分配抖动关注单位时间创建大量短命对象。即使对象最终都能回收，创建、追踪和回收也会消耗资源，分配压力可能影响帧时间。因此应分别看存活集合趋势与分配速率，不能看到 GC 多就直接下结论“有泄漏”。

**原理与边界：** 对象复用也有代价：复杂池化会延长存活、保留大数组或引入同步错误。先定位热路径，如每帧创建大量临时集合，再比较可读改造的测量结果。与 [手册 C42](android-interview-handbook.md#q-c42) 的引用链排查互补。

**追问：** 手动调用 System.gc 能作为修复吗？ **答：** 它不是可预测的资源或时序控制，不能替代减少无效分配、解除引用及测量；可能还干扰分析。

**常见误区：** 只统计 GC 次数，不观察暂停、总耗时、分配量、帧时间和设备条件。

**官方依据：** [Android 堆分析中的分配压力与 GC 暂停说明](https://developer.android.com/studio/profile/capture-heap-dump)；[Android 内存管理概览](https://developer.android.com/topic/performance/memory-overview)。

<a id="ja24"></a>
### JA24 P0 JVM 内存区域知识怎样用于 Android 而不混淆 ART

**口述回答：** JVM 规范的栈、堆、方法区等是理解执行与数据生命周期的抽象入口；HotSpot 的具体布局、收集器和命令参数不是所有运行时的共同实现。Android 常规 Java/Kotlin 构建生成 DEX，设备由 ART 执行；开发机上的 Gradle/JDK 与手机运行时不是同一套进程。

**原理与边界：** ART 可以结合解释执行、JIT 和 AOT，不能说“ART 永远纯 AOT”。分析 Android 卡顿或内存应使用对应设备的工具与版本信息，而不是将桌面 JVM 调参经验直接粘贴。与 [Q039](../questions/07-Java集合与JVM/Q039-JVM-的运行时数据区怎样划分.md)、[手册 C46](android-interview-handbook.md#q-c46) 相衔接。

**追问：** 开发机改成 JDK 21 后手机就拥有 Java 21 全部 API 吗？ **答：** 不会，构建运行 JDK、语言特性、库 API 和设备支持需要分别判断，见 JA40。

**常见误区：** 用“都是虚拟机”推导堆布局、GC 日志、性能优化完全相同。

**官方依据：** [Android ART 与 DEX 概览](https://source.android.com/docs/core/runtime)；[ART 的 JIT 与 AOT 配合](https://source.android.com/docs/core/runtime/jit-compiler)。

<a id="ja25"></a>
### JA25 P1 类的静态初始化为什么会影响首次调用和失败行为

**口述回答：** 加载、链接与初始化不是同一阶段；类初始化执行静态字段初始化和静态块，并有规定的同步过程。把磁盘、网络或复杂依赖藏在静态块里，会让首次主动使用的线程承担开销或等待，还可能形成初始化依赖问题。应把耗时初始化放到有明确结果与失败反馈的入口。

**原理与边界：** 使用编译期常量和读取普通静态字段的初始化触发规则不同。初始化异常可能使该类在相应加载器下进入错误状态，后续使用不应被当作“重新跑一次静态块”重试。静态单例初始化也不能自动解决 Activity 生命周期。

**追问：** 首次加载类就一定执行所有静态代码吗？ **答：** 不能把加载与初始化混为一谈；要按创建实例、调用静态方法、访问非编译期常量静态字段等触发规则分析。

**常见误区：** 认为 static 初始化没有线程与时延问题，或认为静态块失败后每次调用都会自动恢复。

**官方依据：** [JLS 12.4 初始化触发与详细过程](https://docs.oracle.com/javase/specs/jls/se17/html/jls-12.html#jls-12.4)。

## 进阶追问（JA26–JA40）

<a id="ja26"></a>
### JA26 P1 预估 HashMap 容量时为什么既不能越大越好也不能只填元素数

**口述回答：** 初始容量与能容纳的映射数不同，扩容还受负载因子影响。预估数量合理时，可以减少反复重建内部结构；过大又会浪费空间，并可能提高遍历成本。哈希分布不均还会增加查找工作，所以容量规划、键质量和访问模式必须一起分析。

**原理与边界：** Java SE 17 HashMap 文档指出遍历成本与容量加映射数有关。桶结构、树化阈值和迁移细节要固定实现版本再讲，不能把某篇 HotSpot/JDK 源码文章当所有 Android 版本的实现。相比 [Q035](../questions/07-Java集合与JVM/Q035-HashMap-如何定位元素并处理冲突和扩容.md)，这里先判断调优目标。

**追问：** 大量键的 hashCode 一样，增大容量一定能改善吗？ **答：** 不能保证；相同散列值仍可能聚集，首先检查键设计、数据分布和具体实现，再测量。

**常见误区：** 把 O(1) 当无条件最坏情况承诺，或只背某个树化数字来证明性能。

**官方依据：** [HashMap 的容量、负载因子与遍历成本](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashMap.html)。

<a id="ja27"></a>
### JA27 P1 公平 ReentrantLock 为什么仍不能承诺业务严格先来先服务

**口述回答：** 公平锁约束的是特定锁争用规则，不是操作系统调度或整条业务链路的 FIFO。无参 tryLock 可以不遵守公平设置，抢到锁也不表示后续 I/O、回调或任务完成顺序一致。选择锁时先确定是否需要可中断、限时获取和多个 Condition，再权衡吞吐与等待。

**原理与边界：** 成功获取后要在 finally 解锁；只在成功获取后解锁，不能为抢锁失败路径无条件 unlock。`synchronized(lockObject)` 与 `lockObject.lock()` 是两套协议。持有多把锁时仍需一致的顺序，不能靠“使用公平锁”消灭死锁。

**追问：** 限时 tryLock 失败后直接重试就安全吗？ **答：** 不一定，可能活锁或持续占用资源；需要明确总时间预算、已获资源释放和失败反馈。

**常见误区：** 宣称 ReentrantLock 永远比 synchronized 快，或将公平性等同于绝不饥饿的业务保证。

**官方依据：** [Android ReentrantLock 的公平性与 tryLock](https://developer.android.com/reference/java/util/concurrent/locks/ReentrantLock)；[Lock 的同步语义与使用协议](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/Lock.html)。

<a id="ja28"></a>
### JA28 P1 原子更新函数为什么不能顺手发请求和记录不可重复副作用

**口述回答：** `updateAndGet` 等函数式原子更新可能因竞争重试，提供的函数应只计算新值，不能假定只执行一次。把扣费、网络发送或不可重复埋点放进去，可能让状态只提交一次而副作用发生多次。应把原子状态转换与业务副作用及其幂等协议分开设计。

**原理与边界：** AtomicInteger 适合单值原子控制；LongAdder 通过分散更新降低统计热点争用，但 sum 在并发更新期间不是整体原子快照，不适合拿来实现精确限额的“检查再扣减”。CAS 的状态 ABA 还需根据实际算法讨论，不能用计数器替代版本语义。

**追问：** 用 LongAdder 统计请求量后判断小于上限就接收可以吗？ **答：** 不能据此得到严格限流，需要原子的准入状态机或专门协议；统计近似读与控制决策目的不同。

**常见误区：** 认为无锁等于没有重试和成本，或所有原子类都适合维护跨字段事务。

**官方依据：** [AtomicInteger.updateAndGet 的无副作用要求](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/AtomicInteger.html#updateAndGet(java.util.function.IntUnaryOperator))；[LongAdder.sum 的快照边界](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html#sum())。

<a id="ja29"></a>
### JA29 P1 ConcurrentHashMap.computeIfAbsent 为什么不等于业务 exactly-once

**口述回答：** ConcurrentHashMap 提供对应键的原子组合操作，避免普通“查到空再 put”的竞争；但它不是整张表或外部系统的事务。映射函数应短而简单，不在里面执行长网络调用或递归更新相关映射；昂贵初始化更适合先设计在途任务和失败重试协议。

**原理与边界：** 函数返回 null、抛异常或映射之后被移除，后续调用仍可能再次计算，因此不能把一次建值的并发保证推广成收费或发消息永远一次。value 自身若是可变 ArrayList，也不会因存入并发 Map 就自动安全；size 等瞬时聚合结果不宜作关键准入依据。

**追问：** 两个 key 的余额同时更新能靠两个 compute 保证转账原子吗？ **答：** 不能，两个操作间可被其他读写观察；必须设计跨键的一致性协议或使用合适的事务存储。

**常见误区：** 把旧版分段锁当永久契约，把原子容器操作当全部业务的 exactly-once。

**官方依据：** [ConcurrentHashMap 的原子计算与弱一致性](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html#computeIfAbsent(K,java.util.function.Function))。

<a id="ja30"></a>
### JA30 P1 监听器列表为什么要区分快照迭代和同步包装迭代

**口述回答：** CopyOnWriteArrayList 迭代器观察创建时的数组快照，后续增删不会改变该次遍历；适合读多写少且规模合适的清单，但写复制有成本。Collections.synchronizedMap 等包装器只提供相应同步入口，遍历视图时仍要按文档锁住返回的包装 Map，而不是任意锁 keySet。

**原理与边界：** 快照只复制容器层，不冻结监听器对象状态；移除监听器后，已经取得的快照仍可能回调它。UI 退出时若要求不再接收结果，需要取消标记或生命周期检查，不能把 remove 返回当所有在途通知停止。

**追问：** 为避免持锁回调，可先复制监听器再在锁外调用吗？ **答：** 可以作为设计方向，但要接受该批通知的快照语义，并单独处理监听器失效、异常和重入。

**常见误区：** 对 CopyOnWrite 迭代器调用 remove，或包装 Map 后仍从原始 Map 引用绕过同步。

**官方依据：** [CopyOnWriteArrayList 的快照迭代器](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html)；[Collections.synchronizedMap 的遍历要求](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#synchronizedMap(java.util.Map))。

<a id="ja31"></a>
### JA31 P1 ThreadLocal 为什么可能在线程池里串数据并留住 Activity

**口述回答：** ThreadLocal 的值属于线程，而线程池线程会复用，不属于某次任务或某个页面。如果任务把 Activity 或请求上下文放进去后不清理，下个任务可能读到旧值，长寿命线程也可能延长该值的存活。任务边界应在 finally 中 remove，或选择显式传参和更短生命周期的数据。

**原理与边界：** ThreadLocal 不让共享对象自动变成线程安全：两个线程各自取到的值如果仍指向同一个可变对象，竞争依旧存在。不能依赖线程很快结束或 GC 自动及时清理；键的内部引用形式也不能替代值的所有权分析。

**追问：** 切到另一个线程后还能自动取得原 ThreadLocal 吗？ **答：** 普通 ThreadLocal 没有这种跨线程传播契约；异步链路应显式定义上下文传播与清理，不能把线程身份当任务身份。

**常见误区：** 把 ThreadLocal 称为“无锁共享变量”，或在 Application 静态字段中长期存放页面上下文。

**官方依据：** [ThreadLocal 的线程副本、存活和 remove 语义](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/ThreadLocal.html)。

<a id="ja32"></a>
### JA32 P1 shutdown、超时和 cancel 怎样组成完整的任务终止协议

**口述回答：** shutdown 拒绝新任务并继续已提交任务，本身不等待终止；shutdownNow 尝试中断运行任务并返回未启动任务，也不保证所有工作停止。Future.get 超时只结束等待，cancel(true) 也只是请求取消并允许尝试中断。完整协议还要定义任务如何退出、资源谁释放、迟到结果谁忽略。

**原理与边界：** 页面生命周期不应无条件关闭应用共享线程池；应由资源所有者关闭，并在合适后台边界限时等待。Android 的 ExecutorService.close 在官方 API 中标为 API 36，且会等待终止，不能把 JDK 21 的 try-with-executor 示例当所有设备可用或适合主线程。

**追问：** cancel 成功后能断言远端写入已回滚吗？ **答：** 不能，本地 Future 状态不等于远端事务结果；需要请求 ID、幂等、结果核对或补偿。与 [SDK 的超时/迟到结果](sdk-source-deep-dive.md) 作为概念对照，不能混用实现。

**常见误区：** 页面销毁就“杀掉线程”，或通过无限 awaitTermination 把主线程卡住。

**官方依据：** [Android ExecutorService 的关闭与 API 36 close](https://developer.android.com/reference/java/util/concurrent/ExecutorService#close())；[Future 的超时与取消](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Future.html)。

<a id="ja33"></a>
### JA33 P1 CompletableFuture 怎样避免嵌套 Future 和错误的执行线程

**口述回答：** thenApply 变换结果，函数本身返回异步阶段时用 thenCompose 展平依赖；两个独立阶段的组合可选择对应组合 API。非 Async 回调不承诺新线程，Async 也要明确执行器；耗时计算和 UI 更新应在各自合适的调度边界，不能在主线程 join 等待。

**原理与边界：** 异常恢复要决定返回默认值、转失败还是继续传播，不能用 exceptionally 把所有故障涂成成功。CompletableFuture.cancel 主要使结果异常完成，并不控制所有底层计算，中断参数不能被当成停止 I/O 的保证。相较 [XML 指南 Q25](word-crush-android-xml-guide.md#q25)，这里强调依赖图与执行器，而非声称旧项目已使用它。

**追问：** Async 一定是应用专用后台池吗？ **答：** 不是，不传执行器时受该 API 默认执行策略约束；资源隔离、线程数和生命周期都要显式考虑，并核对 Android 可用 API。

**常见误区：** 把 thenApplyAsync 当完整线程策略，或看到 Future 异常完成就断言远端任务停止。

**官方依据：** [CompletableFuture 的依赖、执行策略与取消](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletableFuture.html)。

<a id="ja34"></a>
### JA34 P1 final 字段的初始化安全为什么仍要求构造期不泄漏 this

**口述回答：** final 不只是禁止再次赋值；正确构造对象时，JMM 对 final 字段的初始化可见性有特殊保证。但构造器里把 this 注册到全局监听器、启动使用它的任务或调用会泄漏自身的外部方法，可能让其他线程看到尚未构造完成的对象，破坏原本推理前提。

**原理与边界：** final 引用不冻结其对象后续变化。构造时做好防御性复制、完成不变量后再发布，比只给字段加 final 更完整；常规跨线程交付仍应使用清晰的安全发布机制，而不是把 final 当对整张对象图的万能屏障。

**追问：** 构造器调用可被子类重写的方法还有什么问题？ **答：** 可能执行子类逻辑时子类字段尚未初始化，触发错误或再次泄漏；初始化阶段尽量避免这种可扩展调用。

**常见误区：** “所有字段 final，所以内部列表可以随便并发改”，或“构造器尚未返回也已足够安全”。

**官方依据：** [JLS 17.5 final 字段与正确构造](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html#jls-17.5)；[JLS 12.5 实例创建与初始化顺序](https://docs.oracle.com/javase/specs/jls/se17/html/jls-12.html#jls-12.5)。

<a id="ja35"></a>
### JA35 P1 同名类为何可能不能互相强转且各有一份静态状态

**口述回答：** 在 JVM 类型模型中，类身份除了二进制名称，还包括定义它的类加载器。两个不同定义加载器各自定义同名类，仍可形成不同运行时类型，因此名字一样也可能 ClassCastException，各自静态字段也不是同一份。排障要看类名、实际加载器与对象来源。

**原理与边界：** “不同加载器发起加载”不一定得到不同类型，因为委派后可能由同一个定义加载器定义。Android 的 DEX/类加载实现要查对应平台，不能将 Java SE 的加载启动流程原样当 Android 应用入口。这也解释了某些“单例”只在特定类身份范围内成立。

**追问：** 插件对象为什么能通过宿主接口传递？ **答：** 需要双方共享兼容的接口类型身份，并明确实例归属；只让接口源码相同不够。

**常见误区：** 把包名加类名当跨所有加载器唯一标识，或把热加载场景结论推广到每个普通 App。

**官方依据：** [JVMS 5.3 类身份与定义加载器](https://docs.oracle.com/javase/specs/jvms/se17/html/jvms-5.html#jvms-5.3)。

<a id="ja36"></a>
### JA36 P1 WeakHashMap 和 ReferenceQueue 为什么不能替代显式生命周期

**口述回答：** WeakHashMap 的键不会仅因映射而强可达，但 value 仍可能强持有键，间接阻止清理；回收时机也不是业务定时器。ReferenceQueue 可观察引用处理相关通知，却不能提供“页面退出立即执行清理”的承诺，确定释放资源仍需关闭或取消协议。

**原理与边界：** 使用引用队列时还要保留相应 Reference 对象本身，否则它可能先变得不可达而收不到期望通知。弱引用读取后结果可能为 null，且其他强引用依然决定存活；“只加 WeakReference”并不能修复长任务继续工作或反复回调的问题。

**追问：** map 的 value 是捕获 Activity 的监听器，key 也是 Activity，会怎样？ **答：** value 经闭包或字段强持有 key，形成从 map 到 Activity 的强路径；键弱化本身不能切断它。

**常见误区：** 把软引用当固定容量图片缓存，或把 GC 通知视为可预测的资源析构时机。

**官方依据：** [WeakHashMap 的值与键引用限制](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/WeakHashMap.html)；[java.lang.ref 的引用与队列存活规则](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/ref/package-summary.html)。

<a id="ja37"></a>
### JA37 P1 ART 的并发 GC 为什么仍可能影响帧时间

**口述回答：** 并发表示部分工作与应用线程重叠，不代表没有暂停、没有 CPU 竞争或分配等待。分析时要区分暂停时间、GC 总耗时、回收量与当时的分配压力，再关联帧追踪；仅见某条 GC 日志不能证明它就是卡顿根因。

**原理与边界：** AOSP 文档介绍了 ART 的不同 GC 计划及版本演进，例如并发复制与代际机制；这不是对所有设备、厂商配置或未来版本都使用同一收集器的承诺。也不能把 HotSpot 的 G1/ZGC 参数拿来解释手机日志。需要记录实际系统与运行时条件。

**追问：** 看到很短的 pause 但 UI 仍卡，下一步看什么？ **答：** 检查同一时段主线程执行、锁等待、分配等待及其他 CPU 负载；GC 总时长和单次暂停不是同一个指标。

**常见误区：** “并发 GC 等于零暂停”，或“代际一定让任何工作负载更快”。

**官方依据：** [AOSP ART GC 计划与日志分析](https://source.android.com/docs/core/runtime/gc-debug)。

<a id="ja38"></a>
### JA38 P1 Android 内存排查为什么不能只找最大的 Java 对象

**口述回答：** 要先明确异常现象和内存口径，再看对象数量、浅大小、保留关系及到 GC Root 的路径。浅大小小的持有者可能留住很大对象图；进程内还有 native 分配、映射和其他资源，单个 Java 堆视图不能证明全部内存都健康。重复操作后的趋势比一张孤立截图更有说服力。

**原理与边界：** 大对象可能是合理缓存，销毁页面的持续保留才需要结合所有权判断；反过来 native 资源泄漏也不能只靠 Java 可达性解决。堆转储和分析本身会干扰运行，采样条件、构建类型和设备要记录，不能拿分析时的延迟直接当线上帧时间。

**追问：** 清空某个集合后内存没立刻下降能断言泄漏吗？ **答：** 不能，还要区分其他引用、GC 时机、运行时保留可复用堆空间和进程统计口径，再沿引用链验证。

**常见误区：** 把高内存一律归为泄漏，或把 OOM 与系统因整体内存压力终止进程当同一事件。

**官方依据：** [Android 堆转储与对象保留分析](https://developer.android.com/studio/profile/capture-heap-dump)；[Android 内存分配与进程管理](https://developer.android.com/topic/performance/memory-overview)。

<a id="ja39"></a>
### JA39 P1 JNI 中局部引用、全局引用和 native 缓冲区该怎样分开管理

**口述回答：** JNI 引用是受 VM 管理的对象引用句柄，不是可以随意保存的 Java 对象裸地址。局部引用有调用与线程范围，全局引用需成对删除；取得数组或字符串数据还要按相应 API 释放，不能用“Java 有 GC”替代 native 所有权协议。接口设计应标清谁创建、谁持有、谁结束。

**原理与边界：** JNIEnv 与线程相关，不能直接跨线程复用；native 线程附加到 VM 后，也要处理本地引用积累与退出清理。Get...Elements 可能复制或采用其他策略，不能假定永远零拷贝。现有 [Rust SDK 导读](sdk-source-deep-dive.md) 主要是 Flutter C ABI/FFI，不应改称 JNI 实现。

**追问：** 全局引用长期持有 Activity 有什么后果？ **答：** 它可使对象继续强可达，页面销毁不自动删除该引用；需要按真实所有者在结束路径释放，并检查所有失败分支。

**常见误区：** 保存一个局部引用供稍后异步回调使用，或认为 DeleteGlobalRef 会自动释放独立 malloc 的内存。

**官方依据：** [Android JNI tips 的引用、线程与数组规则](https://developer.android.com/ndk/guides/jni-tips)。

<a id="ja40"></a>
### JA40 P0 使用较新 Java API 前怎样证明 Android 低版本也能运行

**口述回答：** 分别核对运行 Gradle/AGP 的 JDK、源码语言级别、字节码目标、compileSdk 提供的符号，以及 minSdk 设备上的实际库 API。语言特性脱糖与核心库 API 脱糖是不同范围；启用其中一项，不表示自动获得所有新 JDK 类和方法。要查看官方支持表和项目配置，再覆盖目标设备验证。

**原理与边界：** 编译通过只证明当前构建条件能解析和转换，并不独立证明每个低版本运行路径安全。官方 API 的 Added in API level、desugared library 版本及支持列表都需核对；例如 JA32 的 ExecutorService.close 标为 Android API 36，不能因开发机支持它就无条件调用。

**追问：** 把 sourceCompatibility 改成 17 能替低版本补齐全部 Java 17 库吗？ **答：** 不能，sourceCompatibility 约束源码语言级别，targetCompatibility 约束输出 class 文件目标版本；两者都不自动补齐库。库方法可用性仍取决于设备 API、已支持的脱糖范围或明确兼容实现。

**常见误区：** 把 JDK、Java 语言版本和 Android API level 当同一个数字，或把桌面 JVM 测试通过当真机兼容性证明。

**官方依据：** [Android 构建中的 Java/JDK 版本](https://developer.android.com/build/jdks)；[Java 语言特性与 API 脱糖支持](https://developer.android.com/studio/write/java8-support)；[Android ExecutorService.close 的 API 级别](https://developer.android.com/reference/java/util/concurrent/ExecutorService#close())。
