# Word Crush Android XML 与 View 面试问答指南

核对日期：2026-11-01。本文对应 `hejulian2004/word-crush-app` 的 **Java/XML 历史版本** `2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d`。检查时当前 `main` 为 `a4a260740877ac6c1242028caab5c1b6d11c9346`，已经迁移到 Kotlin/Compose，因此不能打开最新 main 就断言下述 XML 实现仍然存在。本文所有项目源码链接固定到历史提交。

这份文档用于 Android 开发实习面试：先用真实调用链理解项目，再练习通用原理和追问。**“源码事实”是静态阅读看到的逻辑；“风险”是需要复现验证的代码路径；“扩展题”不是项目已经完成的功能。** 本次未编译 APK、未运行真机、未测量性能，也不修改应用源码。参考答案不能自动当作你本人独立设计或亲手修复的经历。

官方文档用于解释通用原理，描述的是查阅时的API语义；它不替代本版依赖解析，也不表示本版采用了文档中的所有推荐方案。

## 阅读顺序

1. 先读项目事实表，避免把另一个版本的功能混到当前讲述中。
2. 跟着单词加载、游戏结算、发音播放三条链路找文件。
3. 优先练习 Q01—Q06、Q10—Q13、Q19—Q24、Q29—Q31。
4. MVVM、LiveData、DiffUtil、自定义 View、AIDL 等仍值得学习，但在这个历史版本中未核实到的实现，必须明确作为扩展方案。
5. 完成最后两个真实练习后，再把有证据的过程整理成个人案例。

## 一 项目事实与简历表述核对

| 主题 | 这一历史版本实际看到的内容 | 不应直接声称的内容 |
| --- | --- | --- |
| 页面 | Java、XML、Activity、Fragment、findViewById | 不是这一版中已经实现 Compose 或完整 ViewBinding |
| 导航 | NavHostFragment、NavigationUI、BottomNavigationView、XML nav graph | 不能把使用导航组件说成自研任务栈 |
| 状态组织 | Fragment 字段、回调接口、单例 Server 辅助类 | 未见项目级 ViewModel/LiveData 的 MVVM 链路 |
| 异步 | ExecutorService 单线程执行器、OkHttp enqueue、Handler 回主线程 | 未见 CompletableFuture 作为此版本的异步实现 |
| 列表 | RecyclerView.Adapter、ViewHolder、notifyDataSetChanged/notifyItemChanged | 未见 DiffUtil/ListAdapter 或稳定 ID 策略 |
| 数据库 | Room、Entity、DAO、Gson TypeConverter、数据库版本1 | 未见显式 WAL 调优、迁移方案或吞吐提升测量 |
| 图片 | Glide 加载头像 | 未见项目自行实现 LRU 图片缓存 |
| 音频 | 普通 AudioServer 单例类、OkHttp 下载、MediaPlayer 播放 | AudioServer 不是 Android Service；Manifest 未声明音频 Service 或独立音频进程，未见 AIDL |
| 生命值 | XML 中多个 ImageView，代码替换红白爱心资源 | 未见 LifeRingView 自定义控件 |
| 游戏 | 按钮配对、得分、生命值、CountDownTimer、记录上传 | 不等于已经实现完整状态恢复、可靠离线同步或并发安全 |

若你另外保存了包含 MVVM、LifeRingView、AIDL 的分支、未推送版本或其他仓库，应以那份源码另行核对。这里只说明**本次所选历史提交**，不据此断言你从未做过那些工作。


源码：[AndroidManifest.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/AndroidManifest.xml)；[MainActivity.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Activity/MainActivity.java)；[nav_graph.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/res/navigation/nav_graph.xml)；[WordBookFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/WordBookFragment.java)；[WordBookAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Word/WordBookAdapter.java)；[AppDatabase.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/AppDatabase.java)；[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)；[fragment_time_limit.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/res/layout/fragment_time_limit.xml)。

### 构建声明也要区分声明与实际解析

本版声明 minSdk 26、targetSdk/compileSdk 35、Java 11。依赖中有 OkHttp 4.9.3、Glide 4.15.1、Navigation 2.7.3；Room 显式 2.5.0 与版本目录里的 2.7.1 别名混用。**不能未运行依赖解析就断言最终 Room runtime/compiler 完全一致，也不能仅凭“能写 Java 11 语法”推导所有 Java 库 API 都在所有 Android 版本可用。**

面试可以回答怎样检查 Gradle dependencies/dependencyInsight、编译器与运行库一致性；不能把本次静态检查说成构建成功。


源码：[app/build.gradle](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/build.gradle)；[libs.versions.toml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/gradle/libs.versions.toml)。

## 二 用三条真实链路建立整体理解

### 链路 A 单词本加载与搜索

```text
WordBookFragment.onViewCreated
  → 设置 RecyclerView 与 WordBookAdapter
  → WordServer.loadWordsAsync
      → 单线程 ExecutorService
      → 内存 cachedWords 已加载则返回
      → 否则查询 Room WORDS 表
      → 数据库为空时读取 assets CSV 并批量插入
  → WordCallBack.onSuccess（后台线程）
  → mainHandler.post
  → words.clear/addAll
  → adapter.notifyDataSetChanged
```

这条链路能解释“为什么数据库不在主线程做”“为什么回调仍要切回主线程”“页面退出后结果是否还有意义”。`isLoading` 在这里实际上更接近“已加载标志”，不是一个完整的 Loading/Error/Ready 状态机。

搜索也进入同一个执行器。一个值得验证的细节是：两个 `searchWordsAsync` 重载在结果为空时先调用 `onFailure`，随后没有 return，仍会调用 `onSuccess(emptyList)`。这可能让 UI 先回退加载，再被空列表覆盖。应设计“一个请求只有一个明确终态”的契约，而不是靠调用方猜测。


源码：[WordBookFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/WordBookFragment.java)；[WordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/WordServer.java)；[WordDao.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/Word/WordDao.java)。

### 链路 B 限时游戏配对与保存记录

```text
TimeLimitFragment.onClick
  → 判断第一次选择 / 取消 / 配对成功 / 配对失败
  → 成功时更新按钮、得分、已学单词
  → WordServer.setMaster 异步写入 Room
  → 生命周期暂停、倒计时结束或生命值耗尽时 gameOver
  → saveRecord
  → GameRecordServer.setGameRecordsAsync
      → 后台写入 Room
      → 先回调“本地插入成功”
      → 再 enqueue 上传云端
```

**本地保存成功不等于云端上传成功。** 当前上传结果主要记录日志，没有看到持久化待同步队列、重试退避和服务端幂等协议。可以讨论如何完善，但不能把它描述为已经完成可靠离线同步。

另一个能练习排障的路径在 `setWord()`：遇到已掌握单词时 `i--` 后 continue，没有推进 `wordIndex`。若始终停在同一个已掌握单词，会反复走同一分支。数据少于所需数量、全部掌握也需要单独处理。本次没有运行复现，应把它说成“静态发现的待验证路径”，不是自己的既往修复成果。


源码：[TimeLimitFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/TimeLimitFragment.java)；[WordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/WordServer.java)；[GameRecordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/GameRecordServer.java)；[GameRecordDao.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/GameRecord/GameRecordDao.java)。

### 链路 C 点击发音与释放播放器

```text
WordBookAdapter 的英音/美音点击
  → AudioServer.getAudioServer
  → 新建 OkHttpClient 并 enqueue
  → 回调中将 response body 读为 byte[]
  → mainHandler.post(playAudio)
      → 释放之前的 MediaPlayer
      → 创建缓存临时文件并写入音频
      → 新建 MediaPlayer、setDataSource
      → prepareAsync
      → onPrepared → start
      → onCompletion → release 并删除临时文件
```

这个链路没有 Binder、AIDL 或 ServiceConnection。它很适合讲清网络线程、主线程、文件 IO、MediaPlayer 状态机与请求乱序。

`prepareAsync` 只让准备过程异步，不会把它前面的临时文件写入也移到后台；当前写文件发生在 Handler 投递到的主线程。播放完成有清理，但被新播放替换、网络失败、准备失败和页面离开等路径仍需逐一检查，不能只凭一个 onCompletion 就声称资源管理完善。


源码：[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)；[WordBookAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Word/WordBookAdapter.java)。

## 面试题快速索引

- [Q01 Activity 和 Fragment 各负责什么](#q01)
- [Q02 Fragment 为什么有两个生命周期](#q02)
- [Q03 切后台和旋转屏幕会怎样影响游戏](#q03)
- [Q04 ViewModel 为什么能跨旋转但不能跨进程死亡](#q04)
- [Q05 LiveData 的 setValue 和 postValue 区别是什么](#q05)
- [Q06 Navigation 和 Activity 的任务栈有什么区别](#q06)
- [Q07 XML 布局最终怎样变成屏幕上的界面](#q07)
- [Q08 MeasureSpec 的三种模式是什么](#q08)
- [Q09 invalidate 和 requestLayout 有什么区别](#q09)
- [Q10 事件分发 dispatchTouchEvent intercept 和 onTouchEvent 怎样理解](#q10)
- [Q11 INVISIBLE 和 GONE 有何区别](#q11)
- [Q12 RecyclerView 为什么要有 ViewHolder](#q12)
- [Q13 为什么不能长期保存 onBindViewHolder 的 position](#q13)
- [Q14 DiffUtil 的两个比较分别判断什么](#q14)
- [Q15 notifyDataSetChanged 和局部更新怎么选择](#q15)
- [Q16 Glide 的缓存和自己写 LruCache 是一回事吗](#q16)
- [Q17 Room 比直接 SQLite 多提供了什么](#q17)
- [Q18 为什么数据库放在 Executor 中不等于所有线程问题都解决](#q18)
- [Q19 WAL 是什么 为什么不能说支持多线程同时随意写](#q19)
- [Q20 什么情况下需要事务](#q20)
- [Q21 数据库升级为什么不能只修改 version](#q21)
- [Q22 Gson TypeConverter 和关系表怎么取舍](#q22)
- [Q23 Handler Looper MessageQueue 分别是什么](#q23)
- [Q24 单线程 Executor 是不是天然线程安全](#q24)
- [Q25 CompletableFuture 和回调相比有什么价值](#q25)
- [Q26 OkHttp enqueue 返回成功代表什么](#q26)
- [Q27 为什么旧请求可能覆盖新请求](#q27)
- [Q28 volatile 和 synchronized 分别解决什么](#q28)
- [Q29 MediaPlayer 为什么需要状态机意识](#q29)
- [Q30 prepareAsync 是否意味着整条播放链都不阻塞UI](#q30)
- [Q31 Android Service 与普通 Java 类区别是什么](#q31)
- [Q32 started bound 和 foreground Service 分别是什么意思](#q32)
- [Q33 AIDL Binder Stub Proxy 是怎样配合的](#q33)
- [Q34 Binder 回调线程和进程死亡怎样处理](#q34)
- [Q35 ANR 掉帧 OOM 应怎样区分](#q35)
- [Q36 为什么 GC 不能替代生命周期清理](#q36)
- [Q37 倒计时每秒减一为什么不是可靠计时方案](#q37)
- [Q38 这个项目最值得如何向面试官介绍](#q38)

## 三 Activity Fragment 与状态管理


<a id="q01"></a>
### Q01 Activity 和 Fragment 各负责什么

**参考回答：** Activity 提供应用窗口和组件入口；Fragment 用于组织窗口内可复用的界面与行为，必须依附宿主。Fragment 不是更轻量的独立进程，也没有独立任务栈语义。

**对应项目：** MainActivity 承载 NavHostFragment 和底部导航；单词本、限时游戏分别是 Fragment，排行和登录是独立 Activity。

**继续追问：** 为什么不是每个页面一个 Activity？讨论共享窗口、导航组织和生命周期成本，而不是说 Fragment 永远更快。

源码：[MainActivity.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Activity/MainActivity.java)；[nav_graph.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/res/navigation/nav_graph.xml)；[AndroidManifest.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/AndroidManifest.xml)。


<a id="q02"></a>
### Q02 Fragment 为什么有两个生命周期

**参考回答：** Fragment 对象可能继续存在，但它的 View 树已经销毁；访问 TextView、RecyclerView 的有效期通常到 onDestroyView 为止。异步回调必须判断对应的这次 View 是否仍有效，而不是仅判断 Fragment 对象不为 null。

**对应项目：** WordBookFragment 持有 recyclerView、adapter、searchText 等字段，回调通过 Handler 更新；未看到 onDestroyView 中清理视图引用或取消该页面请求的完整逻辑。

**继续追问：** 只用 isAdded 足够吗？不够，它说明是否附着宿主，不证明结果属于当前 View 实例。改进可用 viewLifecycleOwner、请求代次和释放订阅。

原理：[Fragment lifecycle](https://developer.android.com/guide/fragments/lifecycle)。


<a id="q03"></a>
### Q03 切后台和旋转屏幕会怎样影响游戏

**参考回答：** 切后台、配置变化和进程死亡是不同事件。旋转通常重建 Activity/视图；普通字段不提供完整恢复，进程死亡更会丢失进程内对象。需要明确产品策略，再选择保存轻量状态或持久化业务数据。

**对应项目：** 分数、选中位置、剩余时间等存在 TimeLimitFragment 字段中；onPause 在 score 非零时调用 gameOver。当前没有看到完整 SavedStateHandle 或持久化中的对局恢复。

**继续追问：** 按 Home 应暂停、继续倒计时还是结束游戏？先定规则，再验证，不能靠碰巧触发某个生命周期回调决定产品行为。

源码：[TimeLimitFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/TimeLimitFragment.java)。


<a id="q04"></a>
### Q04 ViewModel 为什么能跨旋转但不能跨进程死亡

**参考回答：** ViewModel 的保留范围由 ViewModelStoreOwner 决定，配置变化时可沿用相应状态；进程结束后对象消失。SavedStateHandle 适合恢复必要的小数据，长期记录仍应落盘。ViewModel 不应长期持有 Activity/View。

**对应项目：** 这份历史实现未采用 ViewModel。可以把游戏状态提取为 ViewModel 作为改进，但不要回答“我已用它保存倒计时”。

**继续追问：** 是不是把整个 Fragment 移到 ViewModel 就完成 MVVM？不是，UI引用、导航与业务状态要重新分责。

原理：[ViewModel overview](https://developer.android.com/topic/libraries/architecture/viewmodel)。


<a id="q05"></a>
### Q05 LiveData 的 setValue 和 postValue 区别是什么

**参考回答：** setValue 在主线程更新；postValue 可从后台安排主线程更新，多次尚未处理的 postValue 可能合并，只观察到最后值。LiveData 是生命周期感知的状态容器，不是可靠的逐条消息队列。

**对应项目：** 当前是回调加 Handler，不是 LiveData。若改造，可让 ViewModel 暴露不可变可观察状态，Fragment 以 getViewLifecycleOwner 订阅。

**继续追问：** 提示、导航是否都塞 LiveData？要先明确状态恢复与事件消费要求，防止重复或遗漏。

原理：[LiveData overview](https://developer.android.com/topic/libraries/architecture/livedata)。


<a id="q06"></a>
### Q06 Navigation 和 Activity 的任务栈有什么区别

**参考回答：** Activity task/back stack 由系统管理；Navigation 管理宿主内的目的地与返回行为。两者相关但不是同一个栈。启动模式和 Intent flags 影响 Activity 复用，不能用来替代 Fragment 目的地状态管理。

**对应项目：** MainActivity 将 BottomNavigationView 绑定 NavController；登录跳转 startActivity 后 finish 当前 Activity。Manifest 未为这些 Activity 显式设置特殊 launchMode。

**继续追问：** singleTop 只保证什么？目标位于栈顶时可复用；不是全应用只允许一个实例。singleTask 等还涉及任务与清栈，不宜无需求乱用。

原理：[Tasks and back stack](https://developer.android.com/guide/components/activities/tasks-and-back-stack)。源码：[MainActivity.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Activity/MainActivity.java)；[nav_graph.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/res/navigation/nav_graph.xml)；[AndroidManifest.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/AndroidManifest.xml)。


## 四 XML View 与自定义绘制


<a id="q07"></a>
### Q07 XML 布局最终怎样变成屏幕上的界面

**参考回答：** LayoutInflater 根据 XML 创建 View 树，随后经历测量、布局和绘制。测量确定尺寸，布局确定位置，绘制把背景、内容和子视图呈现出来。XML 是声明方式，不是脱离运行时的图片。

**对应项目：** 页面通过 inflater.inflate 或 setContentView 创建布局，之后 findViewById 设置文字和监听器。inflate(item,parent,false) 保留从父容器推导 LayoutParams 的机会，而不是立即把 item 加入 RecyclerView。

**继续追问：** 为什么嵌套层级可能影响性能？它会增加遍历与约束计算，但应通过实际布局与测量数据判断，不能仅凭 XML 行数。

源码：[WordBookAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Word/WordBookAdapter.java)；[fragment_time_limit.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/res/layout/fragment_time_limit.xml)。


<a id="q08"></a>
### Q08 MeasureSpec 的三种模式是什么

**参考回答：** EXACTLY 表示父布局给定尺寸；AT_MOST 表示上限，子 View 可以更小；UNSPECIFIED 表示这一维不施加相同的上限约束。MeasureSpec 是父子布局协商输入，不是直接等同 layout_width 的字符串。

**对应项目：** 如果之后将多个爱心改成自定义 LifeRingView，需要处理 wrap_content 的建议尺寸、padding 与不同父约束；当前版本并没有这个自定义控件。

**继续追问：** 父布局给 AT_MOST 但你硬写固定大尺寸会怎样？会破坏期望约束；可根据 desired size 与 resolveSize 类机制求合法尺寸。

原理：[View.MeasureSpec](https://developer.android.com/reference/android/view/View.MeasureSpec)。


<a id="q09"></a>
### Q09 invalidate 和 requestLayout 有什么区别

**参考回答：** invalidate 表示绘制内容失效，需要重绘；requestLayout 请求重新测量与布局。仅颜色、进度变化一般无需主动重新测量，影响大小或位置的属性可能需要布局。两者不是“立即执行 onDraw”的同步调用。

**对应项目：** 生命值当前通过 setImageResource 更新 ImageView。若实现圆环，自定义进度 setter 可以在主线程更新数据并 invalidate；不能声称当前已经做了这种优化。

**继续追问：** 为什么不在 onDraw 每帧 new Paint 或解析资源？热路径分配与重复计算会增加开销，适合初始化或尺寸变化时准备。

原理：[Custom drawing](https://developer.android.com/develop/ui/views/layout/custom-views/custom-drawing)。


<a id="q10"></a>
### Q10 事件分发 dispatchTouchEvent intercept 和 onTouchEvent 怎样理解

**参考回答：** 事件从父到子分发，ViewGroup 可决定拦截，目标处理触摸序列。父容器中途拦截时原子目标会收到取消。返回是否消费会影响后续事件路由；滑动冲突应结合方向和阈值判断。

**对应项目：** 当前主要使用按钮 OnClickListener，未看到复杂自定义手势分发。因此只能作为原理题，不要说项目已实现嵌套滑动算法。

**继续追问：** 只处理 ACTION_UP 是否够？还要考虑 DOWN、MOVE、CANCEL；自定义点击应兼顾 performClick 与可访问性。

原理：[Manage touch events](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)。


<a id="q11"></a>
### Q11 INVISIBLE 和 GONE 有何区别

**参考回答：** INVISIBLE 不显示但保留布局空间；GONE 不占相同布局位置。频繁改变可见性可能引发布局变化，是否合适取决于交互目标。不要把它们等同 alpha 为0。

**对应项目：** 配对成功时按钮被设为 GONE。应观察剩余按钮布局是否符合游戏预期，并用不同屏幕尺寸验证，而不是假设消失只影响绘制。

**继续追问：** 如果想维持棋盘固定网格怎么办？可以考虑保持占位、禁用点击，或者由固定布局管理单元，但这是改进方案。

源码：[TimeLimitFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/TimeLimitFragment.java)；[fragment_time_limit.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/res/layout/fragment_time_limit.xml)。


## 五 RecyclerView 图片与缓存


<a id="q12"></a>
### Q12 RecyclerView 为什么要有 ViewHolder

**参考回答：** ViewHolder 保存一个 item 的视图引用；复用减少反复创建和查找。onCreateViewHolder 创建视图，onBindViewHolder 把当前数据绑定到可能复用过的视图，因此每次绑定都应覆盖所有可变化状态。

**对应项目：** WordBookAdapter 在绑定时设置单词文本和两种掌握按钮的颜色，避免复用时保留上一项的颜色。它是普通 Adapter，不是 ListAdapter。

**继续追问：** 为何图片会串位？除了复用状态，还要检查异步请求目标、旧请求覆盖以及占位图策略。

源码：[WordBookAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Word/WordBookAdapter.java)。


<a id="q13"></a>
### Q13 为什么不能长期保存 onBindViewHolder 的 position

**参考回答：** position 是当次绑定位置；之后插入、删除、重排会改变它。点击时可读取 bindingAdapterPosition 并检查 NO_POSITION，业务操作更适合依赖稳定实体ID。

**对应项目：** 当前按钮监听器捕获绑定时的 position，并调用 notifyItemChanged(position)。当列表更新与点击交错时，应验证是否更新错行；捕获的 Word 对象也可能不再属于最新快照。

**继续追问：** 读取了最新位置就一定正确吗？还要确认当前列表和业务对象一致，并避免对已删除项执行操作。

原理：[RecyclerView.Adapter](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView.Adapter)。源码：[WordBookAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Word/WordBookAdapter.java)。


<a id="q14"></a>
### Q14 DiffUtil 的两个比较分别判断什么

**参考回答：** areItemsTheSame 判断实体身份；areContentsTheSame 判断影响界面显示的内容是否相同。DiffUtil 根据新旧快照计算更新，ListAdapter/AsyncListDiffer 可帮助后台计算；稳定ID是另一项机制，不会自动代替内容比较。

**对应项目：** 当前通过 clear/addAll 和 notifyDataSetChanged 刷新；未使用 DiffUtil。改造时需要保留新旧不可变快照，不能先原地改掉共享 Word 再期待比较发现变化。

**继续追问：** DiffUtil 必然更快吗？比较成本、列表大小、变化比例和移动检测都影响收益，要测量。

原理：[DiffUtil](https://developer.android.com/reference/androidx/recyclerview/widget/DiffUtil)。


<a id="q15"></a>
### Q15 notifyDataSetChanged 和局部更新怎么选择

**参考回答：** 全量通知使列表无法利用精确变化信息；局部通知可缩小更新范围，但索引必须准确。payload 可表达部分字段变化，仍需处理没有 payload 时的完整绑定。正确性优先于减少通知次数。

**对应项目：** 加载与搜索使用 notifyDataSetChanged；掌握按钮使用 notifyItemChanged。若只改变掌握状态，可在未来用 payload 更新按钮，但当前没有该策略。

**继续追问：** 调用通知会自动修改数据吗？不会，数据与通知必须保持一致；先写错集合再通知不会被框架纠正。

源码：[WordBookFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/WordBookFragment.java)；[WordBookAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Word/WordBookAdapter.java)。


<a id="q16"></a>
### Q16 Glide 的缓存和自己写 LruCache 是一回事吗

**参考回答：** 不是。Glide 有活动资源、内存和磁盘等缓存层，缓存命中还受模型、尺寸和变换等键影响；自建 LruCache 只提供容量淘汰容器，需要自己决定键、计量和失效策略。

**对应项目：** 代码调用 Glide 加载头像，未看到手写 LRU。RankingAdapter 每次绑定在头像 URL 后加当前时间，URL不断变化可能削弱复用和缓存命中。

**继续追问：** 如何更新头像又保留缓存？用头像真实版本号或内容签名控制失效，而不是每次绑定制造新URL；效果仍需验证。

原理：[Glide caching](https://bumptech.github.io/glide/doc/caching.html)；[LruCache](https://developer.android.com/reference/android/util/LruCache)。源码：[RankingAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Ranking/RankingAdapter.java)。


## 六 Room SQL 与数据一致性


<a id="q17"></a>
### Q17 Room 比直接 SQLite 多提供了什么

**参考回答：** Room 通过 Entity、DAO 和 Database 组织存储并生成访问代码，能检查许多查询与映射问题；它不是另一种数据库引擎，也不会自动定义业务事务、缓存一致性或网络同步规则。

**对应项目：** AppDatabase 包含 WordEntity 和 GameRecordEntity，WordDao 使用同步返回 List 的方法，Server 用执行器调用。数据库使用 applicationContext 构建。

**继续追问：** Entity 和 UI 的 Word 为什么分开？隔离数据库结构和展示模型有价值，但转换、默认值与身份必须保持一致。

源码：[AppDatabase.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/AppDatabase.java)；[WordEntity.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/Word/WordEntity.java)；[WordDao.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/Word/WordDao.java)。


<a id="q18"></a>
### Q18 为什么数据库放在 Executor 中不等于所有线程问题都解决

**参考回答：** 后台执行解决了阻塞主线程的一部分问题；数据发布、共享可变对象、UI消费和生命周期仍需单独设计。Room 的线程限制也不能保护业务层 ArrayList。

**对应项目：** WordServer 的 DAO 在单线程执行器中运行，但缓存 List 和 Word 对象会交给调用方。单词条目在主线程被修改，之后后台转换写库；跨线程的可变对象边界需要核对。

**继续追问：** 如何改进？在明确边界复制快照或传递不可变命令，再由一个状态所有者完成更新，而不是只给每个字段加 volatile。

原理：[Room asynchronous queries](https://developer.android.com/training/data-storage/room/async-queries)。源码：[WordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/WordServer.java)；[WordBookAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Word/WordBookAdapter.java)。


<a id="q19"></a>
### Q19 WAL 是什么 为什么不能说支持多线程同时随意写

**参考回答：** WAL 把修改先记录到日志，配合 checkpoint 更新主数据库，能够改善许多读写并行场景。但它不等于无限并发写，也不能替代事务和业务互斥。

**对应项目：** AppDatabase 没有显式 setJournalMode；仅凭 .build() 不能说你亲自做了 WAL 调优。默认选择还依赖库与运行环境，应检查实际 journal_mode 后再陈述。

**继续追问：** 为什么有 WAL 仍可能 SQLITE_BUSY？写入竞争、长事务及连接使用策略仍可能造成等待。

原理：[SQLiteDatabase WAL](https://developer.android.com/reference/android/database/sqlite/SQLiteDatabase#enableWriteAheadLogging())。源码：[AppDatabase.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/AppDatabase.java)。


<a id="q20"></a>
### Q20 什么情况下需要事务

**参考回答：** 多步数据库变化必须一起成功或失败时需要事务。多个 DAO 调用按顺序执行，并不自动等于同一个事务；网络请求也不能简单包进长数据库事务来获得分布式原子性。

**对应项目：** 游戏记录本地插入后再上传服务器，两者是不同系统。还要注意 GameRecordDao 删除条件只有 gameType/score/time，未包含读取时使用的 username；多账号场景需要验证归属边界。

**继续追问：** 如何保证离线记录最终上传？可以设计本地事务写记录与待同步任务，再异步重试和服务端幂等；当前未实现这个闭环。

源码：[GameRecordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/GameRecordServer.java)；[GameRecordDao.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/GameRecord/GameRecordDao.java)。


<a id="q21"></a>
### Q21 数据库升级为什么不能只修改 version

**参考回答：** 升级需要让旧结构转换为新结构，并保留必要数据；要测试从已有版本的真实数据库迁移。破坏性重建是有数据丢失后果的选择，不能当作默认修复手段。

**对应项目：** 当前 Database version=1、exportSchema=false，未看到 Migration。以后新增字段、索引或关联表时要补迁移与测试；没有旧版本迁移需求不代表永远不需要。

**继续追问：** 怎样测试？准备旧库数据，执行迁移并检查行数、关键字段、索引以及新的读写行为。

原理：[Room migrations](https://developer.android.com/training/data-storage/room/migrating-db-versions)。源码：[AppDatabase.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/AppDatabase.java)。


<a id="q22"></a>
### Q22 Gson TypeConverter 和关系表怎么取舍

**参考回答：** 把 List 编为 JSON 字符串可简化读写，但对列表元素做筛选、连接和约束不方便；若元素需要独立查询或更新，关系表可能更合适。选择应跟查询需求一致。

**对应项目：** Converters 用 Gson 处理 List<String>，游戏记录含已学单词列表。转换能成功并不说明损坏JSON、空值和未来字段变化都已处理。

**继续追问：** LIKE 模糊搜索为什么可能慢？前置通配符通常不利于普通索引的前缀查找，应结合数据规模与查询计划，必要时评估全文检索。

源码：[Converters.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/Converters.java)；[WordDao.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/Word/WordDao.java)。


## 七 线程 网络与异步结果


<a id="q23"></a>
### Q23 Handler Looper MessageQueue 分别是什么

**参考回答：** Looper 驱动某线程的消息循环，MessageQueue 保存待处理消息，Handler 向关联队列投递任务或处理消息。Handler 不会自动创建新线程；绑定主 Looper 的任务仍在主线程执行。

**对应项目：** WordBookFragment 用主线程 Handler 更新列表，AudioServer 用它播放音频，但也把临时文件写入带到了主线程。

**继续追问：** 为什么 post 后不保证马上执行？前面的消息、主线程忙碌和调度会影响执行时机。

原理：[Handler](https://developer.android.com/reference/android/os/Handler)。源码：[WordBookFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/WordBookFragment.java)；[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)。


<a id="q24"></a>
### Q24 单线程 Executor 是不是天然线程安全

**参考回答：** 它只串行执行通过同一个执行器提交的任务；其他线程直接读写同一对象仍可能竞争。任务异常、队列积压、取消和所有者退出也需要处理。

**对应项目：** WordServer 和 GameRecordServer 各有单线程执行器，并不是整个应用只有一个线程。WordServer 嵌套提交任务，外层返回不代表内部后续任务已经完成。

**继续追问：** 为什么不能在这个执行器任务中等待同一执行器的另一个 Future.get？后续任务排在队列中却被当前任务等待，可能死锁。

源码：[WordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/WordServer.java)；[GameRecordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/GameRecordServer.java)。


<a id="q25"></a>
### Q25 CompletableFuture 和回调相比有什么价值

**参考回答：** 它可以表达依赖组合、成功变换和异常恢复。thenApply 不承诺另起线程，Async 变体的执行器选择也必须明确；不要在主线程 get/join 阻塞等待。取消 Future 不自动保证底层网络或IO已中断。

**对应项目：** 这个版本未使用 CompletableFuture；只可作为未来整理回调链的选择，不可说已完成该改造。

**继续追问：** 改成 Future 就有生命周期了吗？没有，页面离开后仍需取消、忽略旧结果或由更长生命周期状态持有者接管。

原理：[CompletableFuture](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletableFuture.html)。


<a id="q26"></a>
### Q26 OkHttp enqueue 返回成功代表什么

**参考回答：** enqueue 只表示异步调用已提交；HTTP响应、业务状态和本地UI成功是不同阶段。传输失败通常走 onFailure，但HTTP错误状态需要在响应路径检查；还要统一处理响应体关闭和解析异常。

**对应项目：** 多个 Server 使用 enqueue 并自行解析JSON。GameRecordServer 的本地保存回调在网络上传完成之前触发；不能把本地提示解释成远端已同步。

**继续追问：** 为什么建议复用 OkHttpClient？连接池、线程调度等资源可共享；当前多个方法每次创建Client，应评估生命周期与配置统一。

源码：[GameRecordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/GameRecordServer.java)；[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)。


<a id="q27"></a>
### Q27 为什么旧请求可能覆盖新请求

**参考回答：** 异步完成顺序不等于发起顺序。取消是优化，结果归属校验仍有价值；可以给页面查询或播放动作分配递增请求号，只有当前请求能发布结果。

**对应项目：** 发音请求 A 慢、B 快时，B先播放，A后返回又释放当前播放器并播放A。只把播放切到主线程可以串行调用，但不能保证最后一次用户意图获胜。

**继续追问：** 如何测试？fake网络故意按B→A返回，断言最终播放B，并检查A的响应和临时资源被清理。

源码：[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)；[WordBookAdapter.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Word/WordBookAdapter.java)。


<a id="q28"></a>
### Q28 volatile 和 synchronized 分别解决什么

**参考回答：** volatile 提供可见性与相应有序性，不把读改写组合变成原子操作；synchronized 提供互斥及锁边界的可见性。双重检查单例中的 volatile 有意义，但不代表单例内部所有字段自动安全。

**对应项目：** AppDatabase、WordServer、AudioServer 都有双重检查式单例；cachedWords 是共享可变集合，安全性需单独分析。

**继续追问：** 把isLoading改volatile就能保证缓存读写原子吗？不能，它不能保护清空、填充、返回引用这一组业务操作。

源码：[AppDatabase.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/AppDatabase.java)；[WordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/WordServer.java)；[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)。


## 八 音频 服务与 Binder 扩展题


原理：[Java 内存模型与锁](https://docs.oracle.com/javase/specs/jls/se17/html/jls-17.html)。

<a id="q29"></a>
### Q29 MediaPlayer 为什么需要状态机意识

**参考回答：** setDataSource、prepare/prepareAsync、start、pause、stop、reset、release 只在相应状态下合法。异步准备完成前不能假定可播放；错误、结束和替换播放都要有清理路径。

**对应项目：** AudioServer 正常路径先setDataSource，再prepareAsync，在onPrepared启动；onCompletion释放并删临时文件。它不是独立进程音频服务。

**继续追问：** 旧播放器回调会不会影响新播放器？应使用具体实例或代次核验身份，避免旧回调修改共享的当前播放器引用。

原理：[MediaPlayer](https://developer.android.com/reference/android/media/MediaPlayer)。源码：[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)。


<a id="q30"></a>
### Q30 prepareAsync 是否意味着整条播放链都不阻塞UI

**参考回答：** 不意味着。它只异步准备播放器；之前的下载结果处理、文件写入和配置仍在其调用线程执行。把耗时准备步骤拆开并明确资源归属，比只看到Async名称更重要。

**对应项目：** 当前playAudio由mainHandler调用，创建临时文件和写byte[]也在其中。一次性body.bytes还使业务层持有整段音频，不能称为流式播放。

**继续追问：** 先改哪里？后台写临时文件、主线程按状态操作播放器，并给请求取消/替换配套清理。验证时观察实际耗时，不编造提速比例。

源码：[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)。


<a id="q31"></a>
### Q31 Android Service 与普通 Java 类区别是什么

**参考回答：** Service 是系统管理的组件，需声明并有启动/绑定生命周期；普通类没有这些机制。Service 本身也不是后台线程，其生命周期回调默认在所在进程主线程执行。

**对应项目：** 类名AudioServer只是命名；它不继承Service，Manifest没有相应service声明，因此不能说该版本实现了后台服务保活或跨进程音频。

**继续追问：** 有何实际需要才拆Service？跨页面持续播放、可绑定控制等；不要只为简历增加组件。

原理：[Bound services](https://developer.android.com/develop/background-work/services/bound-services)。源码：[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)；[AndroidManifest.xml](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/AndroidManifest.xml)。


<a id="q32"></a>
### Q32 started bound 和 foreground Service 分别是什么意思

**参考回答：** started描述由启动请求驱动，bound描述客户端绑定关系，二者可以同时存在；foreground是以用户可感知通知承担特定工作的运行方式，不是独立线程类型。它们都受系统生命周期与后台限制影响。

**对应项目：** 本版没有这些实现；若扩展为后台音频，需要按目标Android版本核对前台服务类型、权限、启动条件及通知，不能照搬过时保活套路。

**继续追问：** 最后一个客户端解绑是否必然销毁？纯绑定与已经启动的服务不同，应先看实际启动方式。

原理：[Bound services](https://developer.android.com/develop/background-work/services/bound-services)。


<a id="q33"></a>
### Q33 AIDL Binder Stub Proxy 是怎样配合的

**参考回答：** AIDL描述跨进程接口，生成的Stub负责服务端分发，Proxy把调用参数打包并通过Binder发送。跨进程不是共享普通对象引用，要考虑序列化、异常、对端死亡和调用成本。

**对应项目：** 这是扩展知识，不是本版现有调用链。真正拆音频进程时，还需Manifest进程配置、bindService与ServiceConnection，而不是仅创建一个aidl文件。

**继续追问：** 同进程与跨进程调用线程一样吗？不一定；本地接口可能直接调用，远程调用进入服务端Binder线程池，不能默认都在主线程。

原理：[AIDL](https://developer.android.com/develop/background-work/services/aidl)；[Processes and threads](https://developer.android.com/guide/components/processes-and-threads)。


<a id="q34"></a>
### Q34 Binder 回调线程和进程死亡怎样处理

**参考回答：** 远程回调可能来自Binder线程，更新UI应调度到主线程；连接断开、RemoteException、DeathRecipient等用于处理失效，重连后要恢复业务状态而非沿用旧引用。多客户端回调还要管理注册和注销。

**对应项目：** 本版尚未实现，不应声称已有RemoteCallbackList或死亡重连。如果做扩展，可只传播放命令和小型状态，避免把大音频byte[]作为Binder消息来回传。

**继续追问：** 为什么服务端状态不能信任客户端顺序？并发客户端与异步完成会交错，需要命令ID、状态机与线程归属；oneway也不等于业务已完成。

原理：[AIDL](https://developer.android.com/develop/background-work/services/aidl)。


## 九 性能 状态正确性与面试取舍


<a id="q35"></a>
### Q35 ANR 掉帧 OOM 应怎样区分

**参考回答：** 掉帧是渲染未赶上时限；ANR是特定系统交互长时间未响应；OOM是内存分配失败。它们可能关联，但不能用同一原因解释全部问题。排查要先看对应堆栈、线程、帧或内存证据。

**对应项目：** setWord已掌握分支可能不推进索引，适合作为主线程循环排查；音频写文件可能增加主线程负担；大CSV和音频整段读入涉及内存。均不能未经测量就写具体性能损失。

**继续追问：** 如果主线程堆栈在等待锁？继续找锁持有者及其IO或远程调用，而不是只看到主线程idle就结案。

原理：[Diagnose ANRs](https://developer.android.com/topic/performance/anrs/diagnose-and-fix-anrs)。源码：[TimeLimitFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/TimeLimitFragment.java)；[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)；[WordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/WordServer.java)。


<a id="q36"></a>
### Q36 为什么 GC 不能替代生命周期清理

**参考回答：** GC回收不可达托管对象，不会替你定义业务取消时机。消息队列、回调、单例和静态字段可能保持对象可达；播放器、文件和连接等资源还需要明确释放。

**对应项目：** 页面回调可能捕获Fragment/Activity；AudioServer静态播放器需释放，临时文件也有自己的生命周期。数据库使用applicationContext只是减少一种持有Activity的风险，不代表整个应用没有泄漏。

**继续追问：** 怎样验证？反复进入退出页面，检查堆引用链、未完成任务和缓存目录，不只观察一次内存曲线下降。

源码：[WordBookFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/WordBookFragment.java)；[AppDatabase.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Database/AppDatabase.java)；[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)。


<a id="q37"></a>
### Q37 倒计时每秒减一为什么不是可靠计时方案

**参考回答：** 界面回调会受调度与主线程繁忙影响；业务倒计时可根据明确的时钟和截止时刻计算剩余时间，UI只是展示。还要区分需要排除休眠的计时、包含休眠的计时与跨进程恢复。

**对应项目：** 本版使用CountDownTimer并记录回调传来的剩余时间。onPause仅在score非零时gameOver，因此开始但尚未得分就离开页面，是一个需要验证定时器清理的场景。

**继续追问：** 是否应该在onPause统一取消？由产品策略决定暂停还是继续，但销毁View后不能继续操作旧timeText。

源码：[TimeLimitFragment.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Fragment/TimeLimitFragment.java)。


原理：[CountDownTimer](https://developer.android.com/reference/android/os/CountDownTimer)。

<a id="q38"></a>
### Q38 这个项目最值得如何向面试官介绍

**参考回答：** 先讲真实功能与一条能展开的实现，再讲已知边界和一次本人完成的验证。技术数量不如对线程、生命周期和失败语义的解释重要。尚未实现的MVVM/AIDL可作为设计题，不能包装成已完成成绩。

**对应项目：** 可选择“Java/XML单词游戏，Navigation组织页面，Room保存单词及记录，执行器处理数据库，RecyclerView展示词表，OkHttp与MediaPlayer实现发音”作为项目事实主线。个人负责范围需要自己补充。

**继续追问：** 最优先改什么？先做终态唯一、页面退出回调/定时器清理、游戏边界数据和发音乱序验证，再根据测量考虑性能与架构重构。

源码：[MainActivity.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Activity/MainActivity.java)；[WordServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/WordServer.java)；[AudioServer.java](https://github.com/hejulian2004/word-crush-app/blob/2a6e102bda5c3e7af8bf0d08f569c5de3d13fc8d/app/src/main/java/com/example/wordcrush/Server/AudioServer.java)。


## 十 六个能变成真实面试案例的练习

以下是**建议新做的练习**，不是已经完成的修复或测试成绩。每个练习记录版本、输入、预期、实际、修改和回归结果。不要在真实账号数据上进行破坏性实验。

### 练习 1 搜索回调只能有一个终态

- 用 fake DAO 或独立测试替身返回空列表。
- 记录一次搜索的 onSuccess/onFailure 次数与顺序。
- 把“无结果”与“查询失败”明确区分，并确保每次请求只发布一种终态。
- **验收：** 无结果只展示空态；异常展示错误；不存在先失败后成功覆盖，多个查询按最新请求归属发布。

### 练习 2 页面退出后的结果和计时器

- 延迟词表加载，立即切换底部页面或返回，再让回调完成。
- 开始限时游戏但不匹配成功任何词，立即退出；同时覆盖已得分场景。
- 记录View创建/销毁代次、回调线程、Timer是否仍活跃。
- **验收：** 不访问已销毁View；旧结果不能覆盖新页面；定时器按照明确策略暂停/取消/恢复，回到页面不会重复运行。

### 练习 3 游戏出题边界与终止性

- 构造0个词、少于6个未掌握词、全部掌握、首个已掌握、词索引恰到末尾等输入。
- 将出题逻辑提取为不依赖View的可测试函数，明确每次循环必须推进什么状态。
- **验收：** 在有限步内返回题目或“词量不足/全部完成”，不死循环、不越界；规则与UI提示一致。
- 静态阅读已经给出可疑分支，但只有亲自复现并验证后，才能讲自己的修复过程。

### 练习 4 RecyclerView 更新与点击一致性

- 加载列表A、搜索得到列表B，同时点击旧条目，覆盖插入/删除/排序后的位置变化。
- 如改用DiffUtil，为新旧列表构造独立快照，测试身份与内容比较。
- **验收：** 更新正确Word ID，不错行；绑定完全覆盖按钮状态；NO_POSITION安全返回；有无payload都能正确显示。

### 练习 5 音频最后一次请求与完整清理

- 用fake下载按“B先返回、A后返回”控制顺序，另测取消、HTTP失败、播放器准备失败、切页与连续点击。
- 给请求分配代次；缓存文件和播放器实例分别记录创建/释放。
- **验收：** 只播放最后一次有效意图；旧响应不替换当前播放；失败/替换路径同样关闭响应、释放播放器并处理临时文件。
- 不要把网络不可用时静默不播放称作“异常已处理”。

### 练习 6 本地记录与云端失败

- 本地插入成功后模拟上传失败、重复响应、应用重启。
- 先验证当前提示语确实只表示本地保存，再设计pending/synced/error状态作为改进。
- **验收：** UI能区分两种成功；重试不会重复产生业务记录；不同用户名的数据不会被误删；若实现待同步队列，验证任务持久性与幂等键。
- 没有服务端配合就不要宣称“严格一次同步”。

## 十一 面试前的真实材料清单

- [ ] 我能打开本文固定历史版本，而不是拿Compose main解释XML代码。
- [ ] 我能从词表页面找到执行器、DAO和UI更新位置，说明每一步线程。
- [ ] 我能解释页面生命周期与异步结果生命周期为什么不一致。
- [ ] 我能区分本地写库成功、网络传输成功、远端业务成功。
- [ ] 我没有把AudioServer误叫Android Service，也没有把Glide说成自己写的LRU。
- [ ] MVVM、LiveData、DiffUtil、WAL、CompletableFuture、AIDL、自定义View若要写成项目成果，有对应版本源码和个人验证证据。
- [ ] 我有至少一个本人实际做过的实验记录，而不是只背本文风险分析。

### 回答不确定问题的方法

“在我这次核对的XML版本中，实际实现是【代码事实】。你问到的【扩展机制】这一版没有采用，我可以解释它的原理和适用条件。如果要引入，我会先验证【具体问题】，再用【可检查的测试】判断是否改善。”

例如：“这一版音频是同进程单例加MediaPlayer，并没有AIDL。若需要跨页面持续播放，我会先评估绑定服务是否足够；只有明确需要进程隔离时才增加跨进程通信，并补上线程切换、死亡重连和资源释放。”

这比把未找到的能力直接套入项目经历更经得起追问。

