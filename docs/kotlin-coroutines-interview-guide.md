# Kotlin 与协程面试补充：从类型边界到 Flow 失效场景

整理与官方资料核对日期：2026-11-01。共 **40 道通用编辑练习题**，分为基础必会 25 题、进阶追问 15 题。P0／P1 是整理者建议的复习顺序，不是企业出题频率、真实面经记录或招聘要求。本文不新增任何公司的确定面试题，也不证明你曾实现、修复或独立设计过对应能力。

本篇侧重 Kotlin/JVM 与 Android 的常见开发边界。官方 API 页面核对时展示的 kotlinx.coroutines 版本为 **1.11.0**；项目实际依赖、编译器选项和平台实现可能不同，使用前要核对目标版本。以下代码是学习示例，本次未编译、运行测试或在真机验证；原理说明不能当作项目已采用这些方案的证据。

原题 [Q028—Q033](../questions/06-Kotlin与协程/README.md) 已介绍扩展函数、型变、高阶函数、作用域函数、协程与线程、挂起状态机；补充题 [E014—E016](../supplements/06-Kotlin与协程/README.md) 已介绍监督关系、热流选型和 CPU 循环取消。本篇从这些入口继续追问类型漏洞、资源所有权、异常路径和订阅语义，避免重复背定义。

涉及具体项目时，先回到 [FeedLine 源码指南](feedline-android-deep-dive.md)、[原手册 C16—C20](android-interview-handbook.md#q-c16) 和 [AI 接管练习册](ai-code-takeover-workbook.md) 核实实际代码与个人参与范围。本文的改进建议不改变那些文档锁定的源码版本与事实边界。

每题先用 30—60 秒讲清“做法、原因、失效边界”，再回答追问；不要把整段文字当成个人经历照背。

## 基础必会（KT01—KT25）

<a id="kt01"></a>
### KT01 P0 判空以后为什么仍不能 smart cast，应该怎样处理可变属性

**口述回答：** smart cast 依赖编译器能证明两次读取之间类型没有变化。局部稳定的 `val` 容易满足条件，可变属性、开放属性或自定义 getter 则可能每次返回不同结果，不能把一次判空当成后续读取的永久保证。需要同一次读取结果时，先存到局部 `val`，再判空或使用安全调用。`?.let` 只是处理这次取得的非空值，不会锁住原对象，也不会让一整项业务变成原子操作。

**原理与边界：** `!!` 是运行时非空断言，不是修复数据契约；属性被其他线程改变时，局部快照只固定引用，不自动保证引用内部状态一致。

**追问：** `val` 属性一定能 smart cast 吗？不一定，开放 getter、可见性和模块边界等都会影响编译器的稳定性判断。要按报错位置核对，不能只看 `val` 关键字。

**常见误区：** 把“编译器不允许转换”解释成 Kotlin 不支持并发，或用重复的 `!!` 掩盖来源可空的问题。

**官方核对：** [Type checks and casts：smart cast 条件](https://kotlinlang.org/docs/typecasts.html#smart-casts)；[Null safety](https://kotlinlang.org/docs/null-safety.html)。

<a id="kt02"></a>
### KT02 P0 Java 平台类型为什么仍能让 Kotlin 出现空指针

**口述回答：** 没有有效空值信息的 Java 类型可能作为平台类型进入 Kotlin。编译器允许把它当可空或非空使用，不等于 Java 实际保证非空。我会在边界明确转成可空模型并校验，或者依据可信的 nullability 注解建立契约。泛型元素也要检查：Java 代码可能把 `null` 放进 Kotlin 认为元素非空的集合，单看外层 `List` 非空并不足够。

**原理与边界：** 注解支持、类型参数空值约束和诊断强度受编译器及配置影响；不能宣称所有 Java SDK 都有同样的空安全保障。

**追问：** 把返回值直接赋给 `String` 是否更安全？它会把失败暴露在赋值或使用边界，但不能创造有效字符串；要先决定缺失数据应该报错、忽略还是显示默认值。

**常见误区：** 认为 Kotlin 源文件里没有 `!!` 就不可能出现 NPE。

**官方核对：** [Calling Java from Kotlin：null safety、platform types 与泛型](https://kotlinlang.org/docs/java-interop.html#null-safety-and-platform-types)。

<a id="kt03"></a>
### KT03 P0 val 和 List 为什么不等于不可变快照

**口述回答：** `val` 限制的是重新赋值，不限制对象内部变化。`List` 暴露只读接口，也不保证底层对象没有其他可变别名。如果仓库把 `MutableList` 作为 `List` 返回，内部后续修改仍可能被调用者观察到。需要快照时要明确复制集合结构，并继续检查元素是否可变；需要长期共享状态时，应设计受控更新和清晰的所有权，不能依赖接口名称推导深度不可变。

**原理与边界：** `toList()` 不会递归复制每个元素；它也不承诺某个具体集合实现或所有并发读写场景的安全性。

**追问：** `val items: List<Item>` 中的 `Item` 可以改变吗？可以，若 `Item` 本身有可变状态，集合接口不会阻止修改它。

**常见误区：** 把只读集合直接当成 StateFlow 状态更新正确、线程安全或不会被外部篡改的证明。延伸见 [KT32](#kt32) 与 [FeedLine 状态问题](feedline-android-deep-dive.md#5-stateflow-与-sharedflow-在这里怎样工作)。

**官方核对：** [Collections overview：只读与可变接口](https://kotlinlang.org/docs/collections-overview.html#collection-types)；[Properties](https://kotlinlang.org/docs/properties.html)。

<a id="kt04"></a>
### KT04 P0 equals 写对了，为什么集合查找或状态比较仍可能出错

**口述回答：** `==` 使用结构相等逻辑，`===` 比较对象身份；它们回答的问题不同。参与散列集合时，还必须让相等对象有相等的 `hashCode`，并避免入集合后修改参与散列的字段。数组内容比较应使用对应的 `contentEquals` 等 API，不能套用普通列表的直觉。排查状态没有变化时，要核对真实的 `equals` 契约、参与比较的字段以及旧对象是否已被原地修改。

**原理与边界：** “两个对象地址不同”不能推出结构不等；“字段看起来一样”也不能推出某个自定义类已经实现结构相等。

**追问：** 为什么可变对象作为 `HashMap` 的 key 有风险？改变散列字段后，对象可能已不在查询所定位的桶中；优先使用稳定的业务 ID 作为 key。

**常见误区：** 为了让 UI 更新而一律改用引用比较，没有先解释哪些变化属于业务上的状态变化。

**官方核对：** [Equality：结构相等、引用相等与数组比较](https://kotlinlang.org/docs/equality.html)。

<a id="kt05"></a>
### KT05 P0 data class 的 copy 和生成方法有哪些不明显的边界

**口述回答：** data class 默认生成的相等、散列、解构、复制等行为主要围绕主构造器中的属性，类体里新增的普通属性不会自动都加入这些规则。`copy()` 创建新外层对象，但复制的是属性值，嵌套可变集合仍可能共享。用于 UiState 时，要让真正影响状态的字段进入明确的数据模型，同时按需要复制被修改的嵌套结构，不能把一次 `copy()` 叫作深拷贝。

```kotlin
data class Cart(val tags: MutableList<String>)

fun shallowCopyExample() {
    val first = Cart(mutableListOf("android"))
    val second = first.copy()
    second.tags.add("kotlin") // 两个 Cart 仍引用同一个 tags
}
```

**原理与边界：** 显式实现或继承的部分方法还可能影响生成规则；示例只说明浅复制关系，不代表已测试任何项目的状态更新。

**追问：** 把 `loading` 放在类体的 `var` 中会怎样？默认生成的 `equals` 不因它变化而改变，依赖相等性合并的消费者可能不会得到预期更新。

**常见误区：** 认为所有 data class 天然不可变，或复制后所有引用都相互独立。

**官方核对：** [Data classes：类体属性与 shallow copy](https://kotlinlang.org/docs/data-classes.html)。

<a id="kt06"></a>
### KT06 P1 设计加载结果时，sealed 和 enum 应怎样取舍

**口述回答：** 状态只有一组固定常量时，enum 简单明确；不同状态需要不同载荷，例如成功包含数据、失败包含错误类别时，sealed 层次能让每种情况表达自己的数据。配合 `when` 的穷尽检查，新增分支可以在编译时提醒调用方补齐处理。但封闭的是当前编译边界内的类型层次，不是服务端永远不会返回未知业务码，因此外部输入仍要有解析和兼容策略。

**原理与边界：** Kotlin 对直接 sealed 子类型有模块、包等约束；跨平台层次另有规则。普通开放子类型的进一步派生不能被想当然地视为全部封闭。

**追问：** 为什么内部 sealed 状态的 `when` 常不写 `else`？可以利用编译器暴露新增情况；面对外部未知输入时，则应先建模未知或解析失败，而不是靠漏分支崩溃。

**常见误区：** 用一个巨大 enum 外加许多可空字段，导致“成功状态却没有数据”等无效组合。

**官方核对：** [Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html)。原概念可回看原手册 C44，本题侧重结果建模边界。

<a id="kt07"></a>
### KT07 P1 value class 能防止哪些错误，为什么不能保证零分配

**口述回答：** 例如用户 ID 和订单 ID 都用字符串表示时，value class 可以建立不同的 Kotlin 类型，减少同类型基础值被误传；`typealias` 只是别名，不能提供这种隔离。Kotlin/JVM 的 value class 通常用 `@JvmInline` 声明，但在可空、泛型或接口等使用场景可能装箱。它改善的是类型表达，不能不经测量就承诺所有调用都没有对象分配或性能一定提升。

**原理与边界：** 类型包装不等于业务验证；若 ID 必须非空、格式正确，仍需明确构造和校验规则。Java 调用还会遇到名称修饰、装箱和公开 API 设计问题。

**追问：** 给 Java SDK 暴露 value class 参数应注意什么？先检查目标编译器生成的 Java 可见签名及互操作支持，必要时提供普通包装入口，不能直接套用 Kotlin 调用示例。

**常见误区：** 把 value class 当成可随意替代实体对象、天然具备深度不可变性的“轻量 data class”。

**官方核对：** [Inline value classes：representation、boxing 与 mangling](https://kotlinlang.org/docs/inline-classes.html)。

<a id="kt08"></a>
### KT08 P0 lateinit 和 lazy 怎样结合生命周期与线程条件选择

**口述回答：** `lateinit var` 表示暂时无法在构造时初始化，调用者仍负责在首次读取前完成赋值；没初始化就访问会失败。它不是自动初始化，也不适用于可空类型或基本类型属性。`lazy` 在首次访问时计算并保存值，JVM 默认模式会同步初始化；其他模式有不同的并发约束。但初始化安全不等于生成对象的所有方法都线程安全，更不代表对象会在页面销毁时自动释放。

**原理与边界：** `lazy` 初始化失败后，后续访问可以重新尝试；捕获 Activity、View 或大对象的长寿命委托仍可能造成错误持有。

**追问：** 为什么不把所有 View 引用都改成 `lazy`？它可能保存首次找到的旧 View，和 Fragment 新建的 View 生命周期不一致；应依据宿主生命周期管理绑定与清理。

**常见误区：** 用 `isInitialized` 检查替代完整的并发或生命周期协议。

**官方核对：** [Properties：lateinit](https://kotlinlang.org/docs/properties.html#late-initialized-properties-and-variables)；[Delegated properties：lazy](https://kotlinlang.org/docs/delegated-properties.html#lazy-properties)。

<a id="kt09"></a>
### KT09 P1 可空接收者扩展和成员函数同名时，调用结果由什么决定

**口述回答：** 扩展函数不会给类增加真实成员，选哪个扩展主要看调用处接收者的静态类型；存在适用的同名成员时，成员优先。可空接收者扩展允许函数体自己处理 `null`，例如 `Any?.describe()`，但对它使用安全调用 `obj?.describe()` 时，接收者为空会直接跳过调用。排查这类代码要把成员分派、扩展选择和安全调用三个机制分开，而不是只看对象运行时类型。

**原理与边界：** 扩展属性没有自己的 backing field；不能把扩展当成可访问 private 状态、替换虚方法或为对象附加存储的手段。

**追问：** `val animal: Animal = Dog()` 调用 `animal.describe()` 为什么不一定选 Dog 的扩展？扩展选择依据声明处可见的静态类型，普通成员虚方法才另有动态分派规则。

**常见误区：** 把“语法像成员”误认为“覆盖了成员”。基础机制见 [原题 Q028](../questions/06-Kotlin与协程/Q028-Kotlin-扩展函数是怎样实现的.md)。

**官方核对：** [Extensions：静态解析、成员优先与 nullable receiver](https://kotlinlang.org/docs/extensions.html)。

<a id="kt10"></a>
### KT10 P1 by 委托为什么不保证代理对象里的所有调用都经过包装层

**口述回答：** 接口委托能把一批接口实现交给另一个对象，减少样板代码，但它仍然是对那个委托对象的方法调用。包装类覆盖某个方法或属性，不会自动改写委托对象内部的 `this` 和自调用。因此给代理层加校验、埋点或权限判断时，必须核对实际调用入口，不能仅凭 `by` 就声称每条路径都会经过包装逻辑。

**原理与边界：** 属性委托是另一种使用 `getValue`／`setValue` 等约定的机制；例如 `observable` 的回调并不自动提供线程互斥或事务回滚。

**追问：** 委托对象内部的方法读取它自己的属性，会读到包装类覆盖的新值吗？通常仍读取委托对象自己的实现；需要改变这种行为时，应显式设计协作接口。

**常见误区：** 把语言级委托等同于运行时拦截所有调用的代理框架。

**官方核对：** [Delegation：覆盖与 delegate 内部调用](https://kotlinlang.org/docs/delegation.html)；[Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)。

<a id="kt11"></a>
### KT11 P1 inline、noinline、crossinline 怎样影响回调保存和 return

**口述回答：** inline 可以把函数体和适用的 lambda 展开到调用点，减少部分函数对象与调用开销，也可能增加生成代码。需要把 lambda 保存或作为普通对象传递时，用 `noinline` 表达它不参与这种展开。`crossinline` 约束不可使用非局部返回，适用于 lambda 还会从其他执行上下文调用的情况；它本身不创建线程，也不表示异步。选择修饰符要先看回调是否逃逸和控制流契约。

**原理与边界：** 普通 inline lambda 中的裸 `return` 在允许的场景可退出外层函数；`return@label` 只退出相应 lambda，不能混讲。

**追问：** 给一个很大的普通函数加 inline 一定更快吗？不一定，代码膨胀、实际调用方式和优化都会影响结果，应以可解释的需求与测量为依据。

**常见误区：** 把 `crossinline` 当成 `noinline` 的同义词。基础成本见 [原题 Q030](../questions/06-Kotlin与协程/Q030-什么是高阶函数，闭包会带来哪些成本.md)。

**官方核对：** [Inline functions：noinline、non-local return 与 crossinline](https://kotlinlang.org/docs/inline-functions.html)。

<a id="kt12"></a>
### KT12 P1 reified 为什么不能完整验证 List 中的泛型元素

**口述回答：** reified 配合 inline，能把调用点的类型信息用于某些运行时检查，解决普通被擦除的类型参数不能直接 `is T` 的问题。但被检查对象自身的嵌套泛型通常仍被擦除：识别到外层是 `List`，不等于验证里面每个元素都是 `String`。处理反序列化、插件输入或不可信容器时，仍要逐层检查和转换，不能把 `as? T` 包装成万能的安全解析器。

**原理与边界：** 描述目标泛型结构的类型信息和验证现有对象内容是两件事；顶层类型检查成功不能证明嵌套数据满足业务 schema。

**追问：** 为什么 `filterIsInstance<List<String>>()` 不应被当作完整的字符串列表校验？它无法仅凭 JVM 的外层实例检查确认列表中所有元素的泛型类型。

**常见误区：** 说 reified 彻底取消了 JVM 泛型擦除。基础型变见 [原题 Q029](../questions/06-Kotlin与协程/Q029-泛型的协变与逆变解决什么问题.md)。

**官方核对：** [Generics：type erasure、type checks 与 reified](https://kotlinlang.org/docs/generics.html#type-erasure)。

<a id="kt13"></a>
### KT13 P1 List 星投影和 MutableList 星投影分别允许做什么

**口述回答：** 星投影表示具体类型参数未知，不是把它随便当作 `Any` 来写入。读取时只能使用上界允许的类型；对常见 `List<*>` 可按 `Any?` 处理元素。`MutableList<*>` 不能安全 `add` 任意元素，包括 `null`，因为真实列表可能要求非空字符串。但 `clear()` 这类不需要提供未知元素类型的操作仍可调用，所以“星投影完全不可修改”也不准确。

**原理与边界：** `List<*>` 不等于 `List<Any>`；无显式上界的 `T` 可以允许可空类型，若契约要求非空，应考虑 `T : Any` 等约束。

**追问：** 为什么把 `MutableList<String>` 当成可写的 `MutableList<Any>` 不安全？接收方就能放入整数，破坏原列表的元素类型约束；只读生产者和可写消费者要分别设计接口。

**常见误区：** 为了消除编译错误使用 unchecked cast，却没有证明所有读写路径都满足真实类型约束。

**官方核对：** [Generics：star projections、type projections 与 upper bounds](https://kotlinlang.org/docs/generics.html)。

<a id="kt14"></a>
### KT14 P1 Unit、Nothing 和可空类型怎样影响分支与提前返回

**口述回答：** `Unit` 是“正常完成但没有有意义结果”的类型，有对应的值；`Nothing` 表示这条执行路径不会正常返回，例如抛异常或提前跳转。于是 `val value = input ?: return` 的右侧不必产生一个和 input 同类型的值。设计 API 时，普通命令可以返回 Unit，失败或永不返回的路径不应伪造成功值，更不能拿 Unit 代替明确的业务结果。

**原理与边界：** `Nothing?` 可以表示 `null`，不等于可以创建一个非空的 Nothing 实例；理解类型关系有助于解释空集合和异常表达式的类型推断。

**追问：** 为什么 `error("missing")` 能出现在很多不同返回类型的分支里？它不正常返回，Nothing 可以适配相应的类型位置；这不意味着异常已经被处理。

**常见误区：** 把 Kotlin Unit 简单说成“没有类型”，或把返回 Unit 的异步提交当成业务完成保证。

**官方核对：** [Returns and jumps：Nothing 类型](https://kotlinlang.org/docs/returns.html)；[Functions：Unit-returning functions](https://kotlinlang.org/docs/functions.html#unit-returning-functions)。

<a id="kt15"></a>
### KT15 P1 给 Java 使用的 Kotlin API，默认参数和异常声明有哪些落差

**口述回答：** Kotlin 调用端方便的默认参数，不代表 Java 自动拥有相应重载；可按需要用 `@JvmOverloads` 生成 Java 可见入口，或显式提供稳定重载。也不能把 Java 调用方式想成 Kotlin 的命名参数语法。Kotlin 不像 Java 那样强制检查受检异常；若希望 Java 调用者看到对应 throws 声明，需要考虑 `@Throws`，但注解本身不捕获异常、不改变业务失败处理。

**原理与边界：** 注解按既定规则生成重载，不是生成所有默认参数组合；增加重载还要考虑签名冲突、调用歧义和二进制兼容。

**追问：** 加 `@Throws` 能让协程异常自动变成 Java 业务回调吗？不能，异常声明和异步 API 适配是不同层的问题，仍须设计结果、取消与执行线程的契约。

**常见误区：** 仅在 Kotlin 测试中调用成功，就宣称 Java SDK 的接口已经验证兼容。

**官方核对：** [Calling Kotlin from Java：overloads generation 与 checked exceptions](https://kotlinlang.org/docs/java-to-kotlin-interop.html#overloads-generation)。

<a id="kt16"></a>
### KT16 P1 object 和 companion object 的初始化安全能推出状态线程安全吗

**口述回答：** 不能。对象声明提供单例式入口，其 JVM 初始化机制与内部业务状态的并发更新是两回事。多个线程对单例里的普通 `counter++` 仍可能竞争。companion object 也是对象，Java 调用时的 `@JvmStatic` 可以生成便捷静态入口，适用的 `@JvmField` 则影响字段暴露；它们都不会为业务方法自动加锁或约束生命周期。

**原理与边界：** 这是 Kotlin/JVM 互操作语境，不应把 JVM 类初始化结论不加区分地外推到所有平台与所有类加载器场景。

**追问：** 常量放进 `const val` 就能随库升级立即改变旧客户端行为吗？编译期常量可能被调用端内联，需要考虑重新编译与 API 演进，不能只替换库文件作保证。

**常见误区：** 把全局单例当成天然合适的 Activity、View、CoroutineScope 或可变缓存所有者。

**官方核对：** [Object declarations and expressions](https://kotlinlang.org/docs/object-declarations.html)；[Calling Kotlin from Java：static methods 与 fields](https://kotlinlang.org/docs/java-to-kotlin-interop.html#static-methods)。

<a id="kt17"></a>
### KT17 P1 集合链改成 Sequence，为什么可能更慢或改变副作用顺序

**口述回答：** 常规集合的多步转换通常逐步生成中间集合，Sequence 则尽可能在终结操作发生时逐元素推进，可能减少中间分配，也改变执行顺序。它会增加迭代与调用开销，小集合或简单计算未必更快；排序等操作仍可能需要收集大量元素。改造时应先看数据规模、短路操作和内存目标，并避免把依赖执行时机的副作用藏进转换函数。

**原理与边界：** 惰性不等于异步、并行或自动切后台线程；重新消费可能重新计算，有的序列也只允许遍历一次。

**追问：** 为什么不能在资源已经关闭后再消费延迟读取的 Sequence？惰性计算可能直到消费时才触及资源，应让真正的遍历处在有效的资源生命周期内。

**常见误区：** 只凭“少创建集合”就报告性能提升，没有相同输入、结果与环境的测量。

**官方核对：** [Sequences：执行顺序、惰性与开销](https://kotlinlang.org/docs/sequences.html)。

<a id="kt18"></a>
### KT18 P0 suspend API 怎样做到 main-safe，而不是要求调用者到处切 IO

**口述回答：** `suspend` 只允许挂起，不会自动搬走其中的阻塞工作。真正执行阻塞 I/O 或重计算的实现，应负责在合适上下文执行，让上层能安全地从 Main 调用。阻塞 I/O 与 CPU 密集计算分别选择合理调度策略，调度器最好可注入以便测试。某个网络库的 suspend API 已经异步，也不代表其后自己的解码、数据库或图片计算都不会阻塞主线程。

**原理与边界：** `withContext` 是有作用域的上下文切换，不是为了摆脱调用者取消而另建一个无主任务。也不需要机械地为每个本身已 main-safe 的调用再套一次 IO。

**追问：** Repository 把慢函数声明成 suspend 就足够了吗？不够，要沿内部实际调用核对阻塞点、调度器和资源清理。

**常见误区：** 把“协程数量多”当成线程资源无限。基础关系见 [原题 Q032](../questions/06-Kotlin与协程/Q032-协程和线程是什么关系.md)。

**官方核对：** [Android：协程最佳实践与 main-safe](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)；[Coroutine context and dispatchers](https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html)。

<a id="kt19"></a>
### KT19 P0 页面、ViewModel 和 Repository 应该由谁拥有 CoroutineScope

**口述回答：** Scope 表达任务的所有者和取消边界，不只是启动协程的工具。只服务某个 View 的工作应随 View 生命周期结束；业务展示任务常由 ViewModel 拥有；Repository 的一次挂起操作通常沿用调用者的结构化并发关系。确实需要超出页面寿命的工作，再由清晰的长寿命组件提供可注入 scope，而不是每次请求悄悄创建 scope 或到处使用 GlobalScope。

**原理与边界：** 应用级 scope 仍依赖进程存在；必须跨进程终止恢复的任务，需要相应持久化与调度方案，不能把“换了 scope”叫作可靠后台任务。

**追问：** 给 `launch` 随手传一个新 `Job()` 有什么问题？可能切断预期的父子关系，让原所有者无法按原逻辑取消和等待，需明确新的所有权而不是用它躲避失败。

**常见误区：** 让数据层长期持有 View 或 Activity 来获得 scope。与 [SDK 资源所有权](sdk-source-deep-dive.md#7-安全停止先停读者再释放被读对象) 的思路可对照，但不能混称为同一实现。

**官方核对：** [Android：协程最佳实践与 external scope](https://developer.android.com/kotlin/coroutines/coroutines-best-practices#creating-coroutines-business-data-layer)。

<a id="kt20"></a>
### KT20 P0 async 的异常为什么可能在 await 之前就影响其他任务

**口述回答：** `async` 返回 Deferred 来表示结果，不意味着所有失败都被隔离到 await。若它是普通父 Job 的子任务，非取消异常仍会沿父子关系传播并导致关联任务被取消，即使调用者还没有 await。根 async 或监督关系下的 async 才要按各自契约观察结果。我会先画父子 Job，再说明结果在哪里等待、错误在哪里转成业务结果，不用一句“async 异常等 await”概括全部情况。

**原理与边界：** 在已经被子任务失败取消的普通父作用域里，给 await 外面补一个 catch，不等于把父 Job 复原为可继续使用的状态。

**追问：** 两个独立面板请求允许一个失败，怎么实现？先用监督策略隔离兄弟失败，再分别观察每个 Deferred 的结果并处理可恢复错误，取消异常仍应传播。

**常见误区：** 认为不调用 await 就没有异常影响，或认为为 async 加 CoroutineExceptionHandler 就能替代结果处理。

**官方核对：** [Coroutine exceptions handling：launch、async 与父子传播](https://kotlinlang.org/docs/exception-handling.html)。

<a id="kt21"></a>
### KT21 P0 两个并行请求应该整体失败还是保留部分结果

**口述回答：** 这是业务语义选择。只有两份数据都有效才能展示时，用 `coroutineScope` 的共同成败语义更直接；某个非取消失败会取消其他子任务，作用域等待收尾后把失败抛给调用者。允许部分成功时可用 `supervisorScope`，但仍必须处理每个子任务的错误。监督只隔离子任务之间的失败，不自动生成默认数据，也不会忽略 block 自己抛出的异常。

**原理与边界：** 两种词法作用域都会等待其子任务。作用域函数把失败重新抛出后，调用方可在适当位置处理；不要笼统说“调用过它，调用者 Job 就永久不可恢复”。

**追问：** 在 supervisorScope 中直接 await 失败结果而不 catch 会怎样？异常会使 block 本身失败，进而取消作用域里剩余任务；独立失败的需求仍未实现。

**常见误区：** 把 Supervisor 当成吞异常开关。先理解 [补充题 E014](../supplements/06-Kotlin与协程/E014-结构化并发和-Supervisor-有什么不同.md)，再用两个请求的失败路径验证。

**官方核对：** [coroutineScope](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/coroutine-scope.html)；[supervisorScope](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/supervisor-scope.html)。

<a id="kt22"></a>
### KT22 P0 runCatching 为什么可能破坏取消，CPU 循环又应该检查什么

**口述回答：** 取消是协作式协议。`runCatching` 会捕获 Throwable，其中包括 CancellationException；如果直接转成默认值，任务可能在已经不该继续时仍执行后续逻辑。需要恢复的业务错误应明确分类，取消异常通常重新抛出。长时间纯计算没有可取消挂起点时，应按合理批次检查当前上下文活动状态，或在合适位置使用 yield，而不是以为函数带 suspend 就会自动停下。

**原理与边界：** `cancel()` 不是强制终止线程。检查粒度需要平衡响应性与成本；吞掉异常和缺少检查是两类问题，都应覆盖。

**追问：** 用 `catch (Exception)` 就避开取消异常了吗？没有，CancellationException 也在常见捕获范围中，仍须保留取消语义。

**常见误区：** 把正常离开页面导致的取消当成网络故障上报和无限重试。基础取消题见 [E016](../supplements/06-Kotlin与协程/E016-为什么取消协程后-CPU-循环仍可能继续.md)。

**官方核对：** [runCatching](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/run-catching.html)；[ensureActive](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/ensure-active.html)。

<a id="kt23"></a>
### KT23 P0 超时以后为什么还要检查资源归属和副作用是否发生

**口述回答：** withTimeout 到期会取消其作用域，实际计算何时停止仍依赖可取消挂起点或协作检查；它不会回滚已经执行的数据库写入、请求或文件操作。尤其在“拿到资源”和“把资源交给调用方”之间，取消可能让正常结果没有送达。我会明确谁负责申请、何时完成所有权转移、未转移时由谁清理，并用覆盖成功、失败与取消的 finally 或资源 API 管理，不能只在成功分支 close。

**原理与边界：** 资源获取 API 也要处理返回前的取消窗口；仅给调用者加一个 nullable 变量，不能自动弥补获取方已经丢失结果的漏洞。

**追问：** `withTimeoutOrNull` 返回 null 一定表示超时吗？如果 block 的正常业务结果也允许 null，就产生歧义；可用明确的结果类型区分成功缺失与超时。

**常见误区：** 看到 TimeoutCancellationException 就断言远端没执行、资源没创建，可以安全重复非幂等操作。

**官方核对：** [Cancellation and timeouts：asynchronous timeout 与资源](https://kotlinlang.org/docs/cancellation-and-timeouts.html#asynchronous-timeout-and-resources)；[withTimeoutOrNull](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout-or-null.html)。

<a id="kt24"></a>
### KT24 P0 finally 中的挂起清理为什么可能失败，NonCancellable 应怎样限制

**口述回答：** finally 会参与取消后的收尾，但在已取消上下文中继续调用可取消的挂起操作，仍可能立即抛出取消异常。必要的挂起清理可放在有限、明确的 `withContext(NonCancellable)` 中；普通非挂起释放不需要一律这样包装。要让清理尽量短、可收敛，并保留原失败信息，不能把整个业务逻辑搬进不可取消区域来“保证成功”。

**原理与边界：** 当前官方文档特别提醒，把 NonCancellable 和另一调度器一次组合切换，返回时仍可能遇到取消；如确需换调度器，可采用外层 NonCancellable、内层再切换的结构并核对目标版本语义。

**追问：** 为什么不能用 `launch(NonCancellable)` 做后台兜底？它可能破坏期望的父子关系和等待语义；清理应属于原操作的收尾，而不是不受控的新任务。

**常见误区：** 宣称 finally 或 NonCancellable 能抵抗进程被杀、设备断电，或者可以无限等待网络完成。

**官方核对：** [NonCancellable](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-non-cancellable/)；[withContext](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-context.html)。

<a id="kt25"></a>
### KT25 P0 普通 collect 为什么不一定随页面 STOPPED 停止

**口述回答：** collect 是否继续，取决于拥有它的协程是否取消或相应收集策略是否停止，而不是 UI 进入 STOPPED 就自动改变所有流。View 页面可用对应的 viewLifecycleOwner 和 `repeatOnLifecycle` 明确开始、取消与重新收集；Compose 可依据合适依赖使用 `collectAsStateWithLifecycle`。还要分开看消费者停止与生产者停止，ViewModel 或共享上游是否继续运行，取决于其 scope 和共享策略。

**原理与边界：** repeatOnLifecycle 再次进入目标状态时会重新执行 block，重复订阅的冷流可能重新请求；它不替代持久化，也不保证一次性事件恰好消费一次。

**追问：** 在同一个 repeat block 里顺序写两个永不结束的 collect 会怎样？第一个会挂起，后面的收集无法开始；需要为独立收集建立相应子协程。

**常见误区：** 把现有 FeedLine 的普通 collect／collectAsState 描述成已经采用生命周期感知方案；实际实现见 [FeedLine 第5节](feedline-android-deep-dive.md#5-stateflow-与-sharedflow-在这里怎样工作)。

**官方核对：** [Android：生命周期感知协程与并行收集](https://developer.android.com/topic/libraries/architecture/views/coroutines-views#restart)；[Android：Compose 状态与生命周期收集](https://developer.android.com/develop/ui/compose/state#other-supported-types)。

## 进阶追问（KT26—KT40）

<a id="kt26"></a>
### KT26 P1 CoroutineExceptionHandler 为什么不能救活失败的协程

**口述回答：** 它处理的是已经无法再按正常调用路径传播的未捕获异常，常用于根协程或监督关系中相应的 launch 任务做记录与上报。被调用时协程已经失败，不能从出错语句继续执行，也不替代局部 try/catch。普通子协程的失败会按 Job 关系交给父级；根或监督 async 的结果仍需要通过 Deferred 处理，不能期待 handler 自动提供一个正常返回值。

**原理与边界：** 恢复策略应放在仍掌握业务语义的位置，例如把可恢复的读取失败转为缓存结果。handler 不是“给每个子任务加一个就相互独立”的隔离机制。

**追问：** supervisorScope 里的 launch 没有处理异常就一定安全了吗？不安全，监督不等于安装了异常处理，未处理异常仍可能走平台的未捕获异常流程。

**常见误区：** 只看到日志被打印就声称异常已经被恢复、兄弟任务和界面状态都正常。

**官方核对：** [CoroutineExceptionHandler API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-exception-handler/)；[Coroutine exceptions handling：supervision](https://kotlinlang.org/docs/exception-handling.html#supervision)。

<a id="kt27"></a>
### KT27 P1 withContext 块已经返回，为什么调用者仍可能拿不到结果

**口述回答：** 涉及调度器切换时，withContext 返回原上下文也要调度；若调用者在这个窗口被取消，结果可能被丢弃并抛出 CancellationException。于是“块已经执行完”与“调用者成功接收结果”不是同一时刻。对普通数据可以接受丢弃，对待关闭资源或已经提交的副作用则要特别设计：资源返回前要有取消清理，业务写入要有可查询状态、事务或幂等协议。

**原理与边界：** 及时取消不是自动事务回滚。也不能将这一特定返回保证不加条件地套到任何没有调度切换的代码上。

**追问：** IO 中已经写库成功，Main 在接收结果前取消，能否直接重试？先核对写入是否幂等、是否已有业务 ID 或结果查询；不能仅凭未收到返回值判断没有执行。

**常见误区：** 用 `isActive` 检查一次就认定随后一定能完成结果交接；检查和交接之间仍有竞争窗口。

**官方核对：** [withContext：prompt cancellation guarantee](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-context.html)。

<a id="kt28"></a>
### KT28 P1 单次回调包装成挂起函数，除了 resume 还要处理什么

**口述回答：** 单次回调可用 suspendCancellableCoroutine 适配，但必须定义成功、失败、取消如何竞争成唯一终态，并在取消时解除回调或取消底层请求。还要考虑重复回调、注册与取消并发，以及返回的是资源时结果未交付的清理。调用过 resume 也不代表调用者一定拿到值，及时取消仍可能赢得返回竞争；适配器要利用 API 支持的取消清理机制管理资源。

**原理与边界：** `if (continuation.isActive) resume(...)` 是检查再操作，不能仅凭它证明重复完成和取消竞争已经消失；底层注册、注销也需要满足线程安全契约。

**追问：** 如果回调会连续产生多次位置更新，还适合单次 continuation 吗？不适合直接反复 resume，应考虑多值流适配，见 [KT38](#kt38)。

**常见误区：** 在取消时只把 UI 隐藏，底层监听器却一直持有页面；或把被丢弃的资源结果当成无需关闭。

**官方核对：** [suspendCancellableCoroutine：取消、资源与回调竞争](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/suspend-cancellable-coroutine.html)。

<a id="kt29"></a>
### KT29 P1 单线程调度器和 limitedParallelism 一为什么不能替代所有 Mutex

**口述回答：** 一个调度视图限制同一时刻的执行并行度，不意味着整个挂起业务期间一直独占它。某个协程挂起后，另一个可以进入并改动状态，因此“检查余额→挂起请求→扣减余额”仍可能交错。Mutex 表达临界区的互斥，原子变量适合较小的原子更新；具体选择要围绕必须整体成立的不变量，而不是只数线程。必要时还要用数据库事务或服务端协议保证跨层一致性。

**原理与边界：** Mutex 是非可重入的；持有它时再次请求同一锁可能挂起。过长临界区，尤其持锁等待慢 I/O，也会影响吞吐和取消后的收尾。

**追问：** StateFlow 的 update 已经线程安全，为什么仍可能需要别的协调？它只保护对应值的原子更新，不覆盖旁边的写库、发请求或多对象不变量。

**常见误区：** 把没有并行执行等同于没有逻辑并发。项目对照见 [FeedLine 第6节](feedline-android-deep-dive.md#6-协程并发与一次真实点赞)。

**官方核对：** [limitedParallelism：不是 mutex](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-dispatcher/limited-parallelism.html)；[Mutex](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-mutex/)。

<a id="kt30"></a>
### KT30 P0 两个界面分别 collect 同一个 Flow，为什么可能发出两次请求

**口述回答：** 对常见冷流而言，Flow 对象描述的是一段可执行的生产逻辑，真正 collect 时才开始运行；多个 collect 可以分别执行这段逻辑。如果 flow builder 中发网络请求，两个消费者可能各请求一次，保存同一个 Flow 引用并不会自动变成共享任务。是否共享应由业务确定，再选择 shareIn 或 stateIn 及其拥有者、启动策略和错误模型。

**原理与边界：** 不是所有 Flow 实现都冷；StateFlow、SharedFlow 等有不同语义。返回 Flow 的普通函数，也不应在创建流之前偷偷执行阻塞 I/O。

**追问：** 冷流重试或者生命周期重建后的重新收集会怎样？上游通常从头重新执行，所以初始化、请求与副作用应可重复，不能假定从上次失败行继续。

**常见误区：** 将“函数返回同一个引用”“只定义一次变量”当成网络调用只执行一次的证明。

**官方核对：** [Asynchronous Flow：cold flows 与 terminal operators](https://kotlinlang.org/docs/flow.html#flows-are-cold)；[Flow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/)。

<a id="kt31"></a>
### KT31 P1 flowOn 为什么只移动上游，emit 里面随意 withContext 又有什么问题

**口述回答：** Flow 有上下文保持约束，collector 应能掌握自己的执行上下文。flowOn 改变它前面上游的运行上下文，不会把后面的所有收集逻辑一起搬走。在普通 flow builder 中切换到其他上下文后直接 emit，可能违反这个约束；应使用正确的上游切换，或者对确实需要多上下文生产的场景选择合适的 channelFlow 等构建方式。

**原理与边界：** 跨调度器的 flowOn 可能通过内部协程和 channel 衔接；取消时在途元素可能没有送达。相邻的部分通道和缓冲操作会融合，不能简单按操作符数量推算缓冲区数。

**追问：** 给 flowOn 传一个新的 Job 能否顺便改变所有权？它不接受包含 Job 的上下文，应通过任务 scope 管理生命周期，而不是滥用调度操作符。

**常见误区：** 声称 `flowOn(IO)` 后 UI collector 可以安全进行任意阻塞操作。

**官方核对：** [flowOn](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html)；[Flow：context preservation](https://kotlinlang.org/docs/flow.html#flow-context)。

<a id="kt32"></a>
### KT32 P0 StateFlow 不刷新和 update 被重复执行，分别是什么原因

**口述回答：** StateFlow 用 equals 进行相等性合并；把同一个可变对象原地改完再赋回去，可能既破坏旧状态快照，又得不到预期发射。应从旧状态计算新的不可变表示，并检查嵌套对象是否仍被共享。`update` 对当前值的更新是原子的，但竞争时计算 lambda 可以重新执行，因此其中应放可重复的状态计算，不能放计费、发请求或只能执行一次的埋点。

**原理与边界：** 慢收集者可以跳过中间值；StateFlow 适合当前状态，不是完整操作日志。API 的线程安全也不保证“状态更新加写库”的整个业务原子性。

**追问：** 给 MutableList 外面包一个新的 data class 就足够了吗？不一定，新旧状态可能仍指向同一列表；还要检查相等逻辑和元素别名，见 [KT03](#kt03)、[KT05](#kt05)。

**常见误区：** 用不断加随机字段强迫刷新，掩盖错误的数据模型。基础选型见 [E015](../supplements/06-Kotlin与协程/E015-StateFlow-与-SharedFlow-怎么选择.md)。

**官方核对：** [StateFlow：equality-based conflation](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)；[MutableStateFlow.update](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/update.html)。

<a id="kt33"></a>
### KT33 P0 SharedFlow 没有订阅者时，extraBufferCapacity 和 tryEmit 到底保证什么

**口述回答：** 没有订阅者时，SharedFlow 只保留 replay 配置允许的最近值；额外缓冲并不是离线事件队列。默认 MutableSharedFlow 没有 replay，也没有额外缓冲，无订阅者时事件会丢失。此时 tryEmit 可以返回 true，却不代表 UI 收到或处理了事件。设计导航、支付完成等事件时，必须明确无订阅、旋转重建、重复消费和进程终止后的语义，关键业务事实更适合可恢复的状态或持久记录。

**原理与边界：** extraBufferCapacity 和溢出策略主要处理有订阅者但消费者落后的场景；不能据此声称获得持久化或 exactly-once。

**追问：** 改成 replay 为 1 就解决了吗？新订阅者会收到重放值，但同一事实也可能再次触发 UI 动作，需要结合业务 ID、状态与消费协议，而不是只改容量。

**常见误区：** 把 emit 正常返回或 tryEmit 返回 true 当成下游副作用已执行成功。

**官方核对：** [SharedFlow：无订阅者行为与默认配置](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)；[tryEmit](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow/try-emit.html)。

<a id="kt34"></a>
### KT34 P1 stateIn 和 shareIn 怎样决定停止、重启、重放与错误传播

**口述回答：** 它们把上游共享到指定 scope，启动与停止还取决于 SharingStarted。选择 WhileSubscribed 时，要明确最后订阅者离开后多久停上游，以及 replay 或状态缓存如何保留，不能机械说所有页面都应该等五秒。共享上游失败会影响拥有它的共享协程，订阅者不会像直接 collect 冷流那样自动收到那个异常；通常要在共享前重试、转换错误状态或发出约定结果。

**原理与边界：** 停止生产和清空重放缓存是不同策略；stateIn 的初始值、当前值和重启后的第一份真实数据也应区分。

**追问：** UI 已停止收集，上游为什么还在请求？先核对 scope 是否仍存活、started 是否为持续策略、是否还有其他订阅者，及停止延迟是否尚未到达。

**常见误区：** 只选一个操作符而不说明任务所有者、重订阅成本和错误显示方式。

**官方核对：** [stateIn](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/state-in.html)；[shareIn](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/share-in.html)；[SharingStarted.WhileSubscribed](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/-companion/-while-subscribed.html)。

<a id="kt35"></a>
### KT35 P1 buffer、conflate、collectLatest 分别会丢什么或取消什么

**口述回答：** buffer 让生产和消费有一定解耦，默认满时会挂起生产者，具体容量和溢出策略要明确。conflate 倾向保留最新待处理值，跳过过时中间值，但不会因此取消当前 collector 正在执行的动作。collectLatest 则在新值到来时取消前一个 action。列表预览、搜索展示与每笔必须完成的支付或审计记录，对丢弃和取消的容忍度完全不同，不能把这些操作符统一叫作性能优化。

**原理与边界：** 取消前一个 action 仍是协作式的；已经落地的副作用不会自动撤销。选择丢弃策略后，要承认它提供的是有损语义。

**追问：** 为什么耗时写库不一定适合 collectLatest？新值可能取消尚未完成的处理，若每次操作都必须提交，需要事务、队列或其他明确的完整处理语义。

**常见误区：** 把 conflate 解释成“每个值都会处理，只是更快”，或认为多加 buffer 就能无限提高吞吐。

**官方核对：** [buffer](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/buffer.html)；[conflate](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/conflate.html)；[collectLatest](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/collect-latest.html)。

<a id="kt36"></a>
### KT36 P0 catch 和 retry 放在不同位置，为什么会改变恢复行为

**口述回答：** 它们针对各自上游工作，不能把 collector 自己的异常也当作上游网络失败来处理。catch 可以发备用值或转换错误，但不意味着失败源流从原位置继续。若先 catch 并成功消化了错误，后面的 retry 就可能没有失败可重试；通常要先定义有限重试策略，再把最终失败转成业务状态。还要明确错误类别、退避、重复请求副作用和取消语义。

**原理与边界：** 用于取消流的取消异常不应被当成普通失败无限重试；retry 也不是自动去重和事务机制。

**追问：** 为什么不能把所有异常都转成空列表？它会混淆“确实没有数据”和“读取失败”，并可能让调用者失去重试、报警或展示错误的依据。

**常见误区：** 在 collect 外面吞掉异常后，认为原来的冷流还会自动继续向这个 collector 发射。

**官方核对：** [catch](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/catch.html)；[retry](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/retry.html)；[retryWhen](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/retry-when.html)。

<a id="kt37"></a>
### KT37 P1 combine 和 zip 为什么都不能自动提供跨来源事务一致性

**口述回答：** combine 使用各来源已经产生的最新值，某个来源更新后可与其他来源旧值组合，因此适合联合显示，但不是原子快照。zip 按对应次序配对，速度不一致时会相互等待，任一流完成后也影响整体完成。这两种组合语义都不保证用户余额和订单列表来自同一事务版本；若业务要求强一致，应由共同状态、数据库事务或版本协议表达。

**原理与边界：** 两个 StateFlow 的赋值分别原子，不代表 combine 不会观察到两次赋值之间的组合；防抖也不能代替正确性约束。

**追问：** 一次操作必须同时改变两个 UI 字段，怎样避免暂时不一致？可把它们放在一个明确的状态对象中进行一次受控更新，再由此派生展示值。

**常见误区：** 把 combine 说成严格一一配对，或把 zip 说成永远保留双方最新值。

**官方核对：** [combine](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/combine.html)；[zip](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/zip.html)。

<a id="kt38"></a>
### KT38 P1 callbackFlow 怎样避免监听器泄漏和悄悄丢掉失败

**口述回答：** 多次回调适合考虑 callbackFlow，通过 channel 向收集方发送值，再用 awaitClose 在取消或关闭时解除注册。需要核对注册与注销是否可能并发，底层 API 是否线程安全，以及发送遇到已关闭通道或缓冲满时怎么办。trySend 的结果要按契约处理，不能只调用它就认定数据必达；缓冲策略和错误关闭方式都应显式设计。

**原理与边界：** callbackFlow 是冷流，不同收集者可能各注册监听器；awaitClose 的清理回调不是任意挂起业务的执行场所，也不让底层资源自动跨进程可靠保存。

**追问：** 页面取消与最后一次回调同时到达，应如何验收？检查监听器最终解除、发送失败有定义、资源只释放一次，且不会更新已经失效的 View；这些是待执行的测试目标，不是本文已验证结果。

**常见误区：** 注册后没有清理监听器，或在通道仍打开时直接结束构建块而触发契约异常；把所有发送失败静默丢弃后仍宣传“事件可靠”。单次回调见 [KT28](#kt28)。

**官方核对：** [callbackFlow：awaitClose、线程安全与缓冲](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html)。

<a id="kt39"></a>
### KT39 P1 runTest 的虚拟时间能证明哪些行为，为什么热流测试可能一直等

**口述回答：** runTest 配合测试调度器可以控制调度和虚拟时间，适合验证超时、取消、重试及状态顺序。测试调度器要共享同一个 scheduler；跑到真实 Default 或其他未接入测试调度器的延迟，不会自动都被跳过。StateFlow、SharedFlow 通常不会正常结束，所以不能无边界地 toList 等完成；应控制收集寿命、只取所需值，或让长期收集属于测试的 backgroundScope。

**原理与边界：** StandardTestDispatcher 中新任务不一定立刻执行，需要适当推进调度或让出执行。虚拟时间测试也不能证明多线程竞争、真机帧率或网络库的真实取消行为。

**追问：** WhileSubscribed 的 stateIn 测试里，只读取 value 为什么可能一直是初始值？没有实际订阅者时，共享上游可能尚未启动；需要按生产策略建立有效订阅，再驱动输入和断言。

**常见误区：** 为了让测试通过随意 sleep，或把单线程可控调度结果当成生产并发已经穷尽验证。

**官方核对：** [runTest](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/run-test.html)；[Android：测试 Flow 与 stateIn](https://developer.android.com/kotlin/flow/test)；[Android：测试协程](https://developer.android.com/kotlin/coroutines/test)。

<a id="kt40"></a>
### KT40 P1 Java 阻塞 API 怎样与协程取消对齐，runInterruptible 又有什么限制

**口述回答：** 把阻塞调用放进 withContext(IO) 可以避免占住 Main，但并不保证协程取消时底层调用立刻停止。JVM 上可为支持线程中断的阻塞 API 考虑 runInterruptible，让取消与 interruption 关联；若底层忽略中断、依赖 native 调用或有自己的取消机制，仍要遵守那个 API 的协议。资源关闭、请求取消和业务副作用是否已发生，也要分别检查，不能把协程 Job 状态当作底层操作的全部状态。

**原理与边界：** 线程中断不是强制杀线程，更不是数据库或远端操作回滚；不支持中断的接口需要合适适配或其他有明确保证的执行方案。

**追问：** 给包装器传一个全新的 Job，是否能“避免取消错误”？可能只是切断调用者取消关系，让资源更难管理；应保留所有权，再按底层 API 明确终止和清理方式。

**常见误区：** 认为所有 Java 阻塞方法都能被 runInterruptible 及时打断，或声称超时返回后底层一定没有继续执行。

**官方核对：** [runInterruptible](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-interruptible.html)；[Android：协程取消最佳实践](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)。

> 复习验收建议：选择 KT05、KT20、KT23、KT33、KT39，各自写出一个会失败的最小场景，再说明预期结果、实际执行环境和仍未覆盖的边界。只有亲自完成后，才把记录补到个人贡献或测试材料中；本文没有替你完成这些实验。
