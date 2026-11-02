# 面经补充：算法口述、边界与 Java 演练

核对日期：**2026-11-02**。本篇新增 **8 道整理者编写的补充练习 AL01—AL08**，来自用户提供的面经题意线索，不是企业官方题库，不证明面试真实性或发生日期，也不进入原 Q 系列三年公开来源数量。原帖 URL 未提供，截图、账号及原文全文不入库；同题只保留一个练习入口。

每题先确定输入约束，再讲不变量、复杂度和反例。本文代码由整理者独立编写，原始题页仅核对问题条件。代码使用普通 Java 标准库，没有 Android 依赖；**Java SE 的测试不代表 Android 兼容性、真机性能或在线评测通过**。

完整实现和可运行断言见 [InterviewAlgorithms.java](../tests/java/InterviewAlgorithms.java)，文中的 Java 片段是该类的成员，文件头需要 `import java.math.BigInteger; import java.util.*; import java.util.concurrent.ThreadLocalRandom;`。AL01、AL07 为概念题，AL08 为条件推理题，均不通过无关代码凑示例。

## 复习导航与去重

- [AL01 排序比较](#al01) → [AL02 快速排序](#al02) → [AL03 最小 k 个数和第 k 大](#al03)。
- [AL04 零钱兑换 II](#al04) → [AL05 最近公共祖先](#al05) → [AL06 矩阵最长递增路径](#al06)。
- [AL07 二叉树分类](#al07) → [AL08 不均匀燃绳计时](#al08)。
- 反转链表继续使用 [Q096](../questions/15-数据结构与算法/Q096-如何原地反转单链表.md)：指针修改前保存后继，空链表返回 null，迭代时间 O(n)、额外空间 O(1)；递归消耗 O(n) 调用栈。面经中的同题不再新增第二张卡片。
- LRU 继续使用 [Q108](../questions/15-数据结构与算法/Q108-怎样设计-LRU-缓存.md)：哈希表定位、双向链表维护访问顺序；更新已有键同样要移动，容量 0、删除头尾和并发复合操作都要单独验证。限定单链表时必须重算删除成本。

## 排序与选择

<a id="al01"></a>
### AL01 P0 怎样比较常见排序算法，而不只背一张复杂度表

**口述回答：** 我先问数据量、是否近乎有序、重复值多少、能否修改原数组，以及是否要求稳定。插入排序适合很小或近乎有序的数据；归并排序容易保证稳定但数组版本通常需要辅助空间；堆排序适合要求最坏 O(n log n) 的比较排序；随机快排平均表现好，但不能承诺最坏 O(n log n)。值域受限的整数才能考虑计数或基数排序，不可拿它们反驳一般比较排序的下界。

**原理与边界：** 下表针对常见教材实现，n 为元素数；“额外空间”不含输入与返回结果，快排包含调用栈。具体库实现可能切换算法，不能把这里的表当成所有 JDK/Android 实现的保证。

| 算法和条件 | 最好情况 | 平均/期望 | 最坏情况 | 稳定性与额外空间 |
| --- | --- | --- | --- | --- |
| 插入排序 | O(n)，已排序 | O(n²) | O(n²) | 正确使用严格比较可稳定；O(1) |
| 选择排序，普通交换版 | O(n²) | O(n²) | O(n²) | 通常不稳定；O(1) |
| 冒泡排序，带“本轮无交换”提前退出 | O(n) | O(n²) | O(n²) | 相等元素不交换时稳定；O(1) |
| 数组归并排序，普通版 | O(n log n) | O(n log n) | O(n log n) | 合并时相等优先左侧可稳定；O(n) |
| 堆排序，普通比较版 | O(n log n) 上界 | O(n log n) | O(n log n) | 通常不稳定；迭代堆调整 O(1) |
| 快速排序，随机基准 | 互异值且均衡划分 O(n log n) | 期望 O(n log n) | O(n²) | 通常不稳定；栈取决于实现 |
| 计数排序，值域宽度 R | O(n+R) | O(n+R) | O(n+R) | 稳定输出版本通常 O(n+R) |

三路快排的全相等输入可以在一轮划分后结束，因此它的最好情况可为 O(n)；不要把互异值的分析机械套到重复值。堆排序的最好情况上界不等于所有输入都需要同样次数比较。

**追问 1：** 稳定到底保留什么？ **答：** 保留“排序键相等”元素的原有相对顺序，不是说排序后的元素位置不变。按分数排序时，可用原顺序保留同分学生的先后。

**追问 2：** `Arrays.sort` 一定是同一种算法吗？ **答：** 否。先区分基本类型数组、对象数组、API 与实现版本；文档中的实现说明不等于不可变的语言规范，对象排序还存在稳定性契约。

**易错点：** 忽略递归栈；把快排平均复杂度说成最坏；把“原地”和“稳定”当成同一个性质。

**官方/原始依据：** [Java SE Arrays：排序契约与实现说明边界](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Arrays.html)。复杂度表与算法取舍为独立推导。

<a id="al02"></a>
### AL02 P0 快排怎样处理重复值、划分不变量和最坏调用栈

**口述回答：** 选择一个基准，把区间划为小于、等于、大于三部分，只递归两侧；相等区间不再处理。随机选基准改善对固定输入的期望复杂度，但最坏时间仍可能 O(n²)。为避免极端划分让调用栈变成 O(n)，每次只递归较小一侧，较大一侧用循环继续。

**不变量：** 循环开始时 `[lo, less)` 小于基准，`[less, scan)` 等于基准，`(greater, hi]` 大于基准，`[scan, greater]` 尚未分类。从右侧换入的值未检查，所以“大于”分支不能同时递增 scan。

```java
public static void quickSort(int[] a) {
    Objects.requireNonNull(a, "array");
    quickSort(a, 0, a.length - 1);
}

private static void quickSort(int[] a, int lo, int hi) {
    while (lo < hi) {
        int pivot = a[lo + ThreadLocalRandom.current().nextInt(hi - lo + 1)];
        int less = lo, scan = lo, greater = hi;
        while (scan <= greater) {
            if (a[scan] < pivot) swap(a, less++, scan++);
            else if (a[scan] > pivot) swap(a, scan, greater--);
            else scan++;
        }
        // Recurse only into the smaller side; iterate over the larger side.
        if (less - lo < hi - greater) {
            quickSort(a, lo, less - 1);
            lo = greater + 1;
        } else {
            quickSort(a, greater + 1, hi);
            hi = less - 1;
        }
    }
}

private static void swap(int[] a, int x, int y) {
    int tmp = a[x]; a[x] = a[y]; a[y] = tmp;
}
```

**复杂度：** 均匀随机选基准，对任意固定的互异输入期望时间 O(n log n)，最坏 O(n²)；全部相等时 O(n)。该实现只递归较小区间，所以即使划分很差，活动调用栈仍为 O(log n)，但这不会消除二次方的比较次数。交换版本不稳定，原地修改输入。

**追问 1：** 随机化已经有了，为何还要控制栈？ **答：** 随机化改善期望，不是最坏保证；小侧递归给出确定的栈深上界。若业务要求最坏时间保证，可用堆排序或带退化保护的混合排序。

**追问 2：** 比较器写 `a - b` 可以吗？ **答：** 对任意 int 不安全，差值可能溢出；本例直接用 `<`、`>`，泛型比较可用 `Integer.compare`。

**边界测试：** 空数组、单元素、已排序/逆序、全相等、大量重复、`Integer.MIN_VALUE/MAX_VALUE`；随机数组与 `Arrays.sort` 对照。50,000 个已排序和全相等元素用于观察是否出现栈溢出，不是性能基准。

**易错点：** 等于区间继续递归；漏处理被交换进来的值；声称三路划分一定最坏 O(n log n)。

**官方/原始依据：** [教材作者仓库的三路快排说明](https://github.com/kevin-wayne/algs4/blob/master/src/main/java/edu/princeton/cs/algs4/Quick3way.java)。本例为独立的整数实现，并增加小侧递归策略；未复制作者实现。原教材网站本次访问返回 403，作者 GitHub 源码可读取。

<a id="al03"></a>
### AL03 P0 返回最小 k 个数且升序，与返回第 k 大有什么区别

**口述回答：** 返回最小 k 个数需要保留 k 项，并满足最终输出顺序。可维护容量 k 的最大堆：比堆顶更小才替换，遍历后从结果数组末尾向前填入堆顶，得到升序。第 k 大则用容量 k 的最小堆，遍历后堆顶就是答案。重复值按排序位置计数，除非题目另说“第 k 个不同值”。

```java
public static int[] smallestKSorted(int[] a, int k) {
    Objects.requireNonNull(a, "array");
    if (k < 0 || k > a.length) throw new IllegalArgumentException("k");
    if (k == 0) return new int[0];
    PriorityQueue<Integer> heap = new PriorityQueue<>(Comparator.reverseOrder());
    for (int value : a) {
        if (heap.size() < k) heap.offer(value);
        else if (value < heap.peek()) {
            heap.poll(); heap.offer(value);
        }
    }
    int[] result = new int[k];
    for (int i = k - 1; i >= 0; i--) result[i] = heap.remove();
    return result;
}

public static int kthLargest(int[] a, int k) {
    Objects.requireNonNull(a, "array");
    if (k < 1 || k > a.length) throw new IllegalArgumentException("k");
    PriorityQueue<Integer> heap = new PriorityQueue<>();
    for (int value : a) {
        if (heap.size() < k) heap.offer(value);
        else if (value > heap.peek()) {
            heap.poll(); heap.offer(value);
        }
    }
    return heap.element();
}
```

**原理与复杂度：** 堆始终保留“已看过元素中最小/最大 k 项”这一不变量。扫描 O(n log(k+1))；最小 k 结果的有序取出 O(k log(k+1))，由于 k≤n，总上界仍 O(n log(k+1))；额外空间 O(k)，原数组不修改。k=0 的最小集合立即返回空数组，第 k 大则要求 1≤k≤n。

**追问 1：** 快速选择会不会更快？ **答：** 随机快速选择期望 O(n)、最坏 O(n²)，但选出的前 k 项不保证有序；还需要对这 k 项排序，期望总时间 O(n+k log k)，并说明是否允许修改输入。

**追问 2：** 遍历 PriorityQueue 能直接得到升序吗？ **答：** 不能，迭代器不承诺堆序遍历结果就是排序序列；必须反复 poll 或另外排序。

**边界测试：** k=0、k=n、k<0、k>n、空数组第 1 大、重复值、负数、极端 int；以整数组排序后截取前缀/对应位置作独立对照。

**易错点：** 忘记“升序”要求；用去重 Set 改变排名含义；最大堆比较器用减法导致溢出。

**官方/原始依据：** [PriorityQueue 的堆顶、迭代顺序与操作复杂度](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/PriorityQueue.html)；[原始第 k 大问题：按排序位置，不要求不同值](https://leetcode.com/problems/kth-largest-element-in-an-array/)。

## 动态规划与树图

<a id="al04"></a>
### AL04 P0 零钱兑换 II 为什么硬币放外层、金额正序

**口述回答：** 这是无限次使用各面额、计算组合数，不是最少硬币数。定义 dp[s] 为只使用当前已处理面额组成金额 s 的方案数，dp[0]=1 表示空组合。每加入面额 c，让 s 从 c 正序走到目标，做 `dp[s] += dp[s-c]`，这样同种硬币可重复使用，但组合只按统一的面额处理顺序生成，不会把 1+2 与 2+1 重复计数。

```java
public static BigInteger countChange(int amount, int[] coins) {
    Objects.requireNonNull(coins, "coins");
    if (amount < 0 || amount == Integer.MAX_VALUE)
        throw new IllegalArgumentException("amount");
    Set<Integer> seen = new HashSet<>();
    for (int coin : coins) {
        if (coin <= 0 || !seen.add(coin))
            throw new IllegalArgumentException("positive, distinct denominations required");
    }
    BigInteger[] dp = new BigInteger[amount + 1];
    Arrays.fill(dp, BigInteger.ZERO);
    dp[0] = BigInteger.ONE;
    for (int coin : coins) {
        for (int sum = coin; sum <= amount; sum++) {
            dp[sum] = dp[sum].add(dp[sum - coin]);
        }
    }
    return dp[amount];
}
```

**原理与边界：** 面额必须正且互不相同；本例拒绝重复面额，避免同值被当成两种硬币。金额 0 返回 1，即空组合；没有可用组合返回 0。普通整数讲解常用 long，但“最终答案放得下 int”不自动证明所有中间状态都不会溢出；本例用 BigInteger 使计数边界明确。匹配原题 int 返回签名时可在最后调用 `intValueExact()`；通用业务仍应限制金额与面额规模，避免不受限内存分配。

**复杂度：** m 种面额、目标 A 时 O(mA) 次状态更新、O(A) 个 DP 单元，另外去重校验 O(m) 空间；若计数最多 b 位，BigInteger 加法的位运算成本还要计入，不能把任意精度加法说成永远 O(1)。

**追问 1：** 金额放外层、面额放内层呢？ **答：** 常见写法会按最后一枚硬币累加，统计有序序列；例如金额 3、面额 1 和 2，会分别计入 1+2 与 2+1。

**追问 2：** 金额倒序呢？ **答：** 每个面额在本轮只能使用一次，变成另一类 0/1 选择问题，不符合无限供应。

**边界测试：** 5/[1,2,5]→4；3/[2]→0；0/[]→1；负金额、零/负/重复面额拒绝；小金额使用“枚举每种面额使用数量”的递归对照；大方案数检验超过 long 时不回绕。

**易错点：** 把 dp[0] 初始化为 0；只背循环顺序不解释状态；混淆组合数、排列数和最小硬币数。

**官方/原始依据：** [LeetCode 518 的组合数和输入约束](https://leetcode.com/problems/coin-change-ii/)；[BigInteger 的任意精度整数语义](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/math/BigInteger.html)。状态转移与循环顺序解释为独立推导。

<a id="al05"></a>
### AL05 P0 普通二叉树的最近公共祖先，节点可能不存在时怎么办

**口述回答：** 先确认是普通二叉树还是二叉搜索树，目标按节点身份还是值比较，以及两个目标是否保证存在。经典递归在保证都存在时可向上传回匹配节点；若一个目标不存在，直接返回另一个会误报。这里选择显式栈建立父映射，确认 p、q 都被找到，再沿祖先链求第一次交点；不依赖值唯一，也避免极深树的递归栈溢出。

```java
public static final class TreeNode {
    public final int value;
    public TreeNode left, right;
    public TreeNode(int value) { this.value = value; }
}

public static TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
    if (root == null || p == null || q == null) return null;
    Map<TreeNode, TreeNode> parent = new IdentityHashMap<>();
    Deque<TreeNode> stack = new ArrayDeque<>();
    parent.put(root, null);
    stack.push(root);
    while (!stack.isEmpty() && (!parent.containsKey(p) || !parent.containsKey(q))) {
        TreeNode current = stack.pop();
        if (current.left != null) {
            parent.put(current.left, current); stack.push(current.left);
        }
        if (current.right != null) {
            parent.put(current.right, current); stack.push(current.right);
        }
    }
    if (!parent.containsKey(p) || !parent.containsKey(q)) return null;
    Set<TreeNode> ancestors = Collections.newSetFromMap(new IdentityHashMap<>());
    for (TreeNode x = p; x != null; x = parent.get(x)) ancestors.add(x);
    for (TreeNode x = q; x != null; x = parent.get(x)) {
        if (ancestors.contains(x)) return x;
    }
    return null;
}
```

**原理与复杂度：** 输入须为无环、无共享子节点的真正二叉树。IdentityHashMap 明确使用对象身份，两个值相同的不同节点不是同一个目标。最坏 O(n) 时间和 O(n) 额外空间；p==q 时，只有该节点确实在树中才返回它；任一目标为 null 或缺失则返回 null。经典题保证 p≠q 且两者都在树中，本例主动扩展了边界，不能倒说原题就要求缺失处理。

**追问 1：** 为什么不按数值分左右？ **答：** 普通二叉树没有 BST 的有序约束，不能靠值缩小范围；若明确是 BST 且规则、身份和存在性已确认，才可利用顺序。

**追问 2：** 同一棵树有很多次查询？ **答：** 可以评估预处理深度、倍增父节点或欧拉序等方案；是否值得取决于树是否变化、查询量和内存预算。

**边界测试：** 分居两侧、一个是另一个祖先、p==q、同值不同节点、一个缺失、null、100,000 节点退化链。

**易错点：** 默认存在却没有说明；把值相同当同一节点；递归 O(h) 空间说成 O(1)。

**官方/原始依据：** [LeetCode 236：目标存在、身份与祖先定义](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/)。父映射扩展实现为独立编写。

<a id="al06"></a>
### AL06 P1 矩阵最长递增路径为什么可以按有向无环图处理

**口述回答：** 每个格子是顶点，只向上下左右值更大的格子连边。严格递增不可能走回原值，所以图无环。可用记忆化 DFS，也可按拓扑层次计算；这里从没有更大邻居的局部最大值开始，逐层删除，反向减少较小邻居的出度，总层数就是最长路径长度。

```java
private static final int[][] DIRECTIONS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

public static int longestIncreasingPath(int[][] grid) {
    Objects.requireNonNull(grid, "grid");
    if (grid.length == 0) return 0;
    if (grid[0] == null) throw new IllegalArgumentException("null row");
    int rows = grid.length, cols = grid[0].length;
    for (int[] row : grid) {
        if (row == null || row.length != cols)
            throw new IllegalArgumentException("rectangular grid required");
    }
    if (cols == 0) return 0;
    int[][] degree = new int[rows][cols];
    ArrayDeque<int[]> queue = new ArrayDeque<>();
    for (int r = 0; r < rows; r++) for (int c = 0; c < cols; c++) {
        for (int[] d : DIRECTIONS) {
            int nr = r + d[0], nc = c + d[1];
            if (inside(nr, nc, rows, cols) && grid[nr][nc] > grid[r][c])
                degree[r][c]++;
        }
        if (degree[r][c] == 0) queue.add(new int[]{r, c});
    }
    int layers = 0;
    while (!queue.isEmpty()) {
        int size = queue.size();
        layers++;
        for (int i = 0; i < size; i++) {
            int[] cell = queue.remove();
            int r = cell[0], c = cell[1];
            for (int[] d : DIRECTIONS) {
                int nr = r + d[0], nc = c + d[1];
                if (inside(nr, nc, rows, cols) && grid[nr][nc] < grid[r][c]
                        && --degree[nr][nc] == 0) queue.add(new int[]{nr, nc});
            }
        }
    }
    return layers;
}

private static boolean inside(int r, int c, int rows, int cols) {
    return r >= 0 && r < rows && c >= 0 && c < cols;
}
```

**原理与复杂度：** 每个格子最多四条边，建立出度和处理队列均 O(mn) 时间，额外空间 O(mn)。每一轮只处理当前队列已有的节点，新变成零出度的节点进入下一轮，形成从更大值向更小值的 DP 层。只允许严格增大；不能走对角线、越界回绕，或把相等值当成下一步。Java 比较使用 `<`、`>`，不用相减。

**追问 1：** 为什么不只是从矩阵最小值出发？ **答：** 最长路径的起点未必是全局最小格子，局部地形可能让更小格子无法进入最长链；需要覆盖所有节点。

**追问 2：** 记忆化 DFS 为什么也正确，风险是什么？ **答：** 缓存“从此格出发的最优长度”，每个状态只计算一次；但最长路径可达 mn，递归可能栈溢出，本实现用显式队列避免该风险。

**边界测试：** 空矩阵、零列、单格、全相等、含极端 int、非矩形输入拒绝；随机 4×4 内矩阵与无记忆的穷举 DFS 对照，1×40,000 严格递增长路径验证没有递归栈。

**易错点：** 使用全局 visited 永久禁止别的起点经过同一格；把“本轮队列长度”随新增节点一起扩大；相等边会破坏无环论证。

**官方/原始依据：** [LeetCode 329：四邻接、严格递增与约束](https://leetcode.com/problems/longest-increasing-path-in-a-matrix/)。拓扑分层证明与实现为独立推导。

<a id="al07"></a>
### AL07 P0 二叉搜索树、完全二叉树、AVL、红黑树和堆怎样区分

**口述回答：** 这些名称约束的是不同维度。二叉树仅要求每节点最多两个孩子；二叉搜索树约束整棵左右子树的键序，普通 BST 可能退化；完全二叉树约束形状，末层从左填充；AVL 和红黑树维护平衡以控制搜索高度；二叉堆同时要求完全形状和父子堆序，适合取极值，不支持像 BST 那样对任意键直接二分搜索。

**原理与边界：** AVL 每个节点两侧高度差至多 1，更新通过旋转维护。红黑树通过颜色不变量约束高度，具体插入删除修复需要单独推导。中文“满二叉树”有时指每个非叶节点恰有两子节点，有时指每层全满；回答前说清使用 full 还是 perfect 的定义，不能只靠中文名判断。完全树不自动是 BST，平衡树也不等于每层全满。

**追问 1：** 堆为什么常用数组？ **答：** 完全树的形状使 0 基下标 i 的孩子可用 2i+1、2i+2 表示，父节点为 (i-1)/2；访问前仍需范围检查，巨大下标运算应防溢出。

**追问 2：** BST 中序为什么有序？ **答：** 在左子树所有键满足左侧规则、右子树所有键满足右侧规则的全局不变量下，左—根—右访问才有序；只检查直接孩子不够。

**易错点：** 把红黑树说成严格高度平衡；把二叉堆和内存堆混为一谈；认为任意二叉树查询都是 O(log n)。

**官方/原始依据：** [NIST 二叉树定义](https://xlinux.nist.gov/dads/HTML/binarytree.html)；[完全二叉树定义与数组表示](https://xlinux.nist.gov/dads/HTML/completeBinaryTree.html)；[AVL 的高度约束和操作复杂度](https://xlinux.nist.gov/dads/HTML/avltree.html)。

## 条件推理与验证

<a id="al08"></a>
### AL08 P1 两根燃烧各需一小时但速度不均匀的绳，怎样测四十五分钟

**口述回答：** 必须先确认允许同时点燃一根绳的两端，而且每段从两侧燃烧的速率可按同一“剩余燃烧工作量”模型相加。起点同时点 A 的两端、B 的一端。A 烧尽经过 30 分钟，此时点燃 B 的另一端；B 剩余单端燃烧时间为 30 分钟，双端点燃后再烧 15 分钟。B 烧尽即总计 45 分钟。

**原理与边界：** 空间位置不是时间比例，不可剪掉四分之一长度冒充 15 分钟。在标准燃绳题的假设下，A 的两火头共同完成相当于单火头 60 分钟的工作，因而耗时 30 分钟；与两火头相遇的物理位置无关。若实际材料从两端燃烧的规律不同、火焰互相影响，或题目不允许两端点火，就不能声称这个方案成立。

**追问 1：** 为什么不能把绳子对折成四段？ **答：** 燃烧不均匀，等长不等时，也不能假设两条绳任意等长段耗时相同。

**追问 2：** 这是不是实验测量结论？ **答：** 不是，是在标准数学模型下的事件计时证明；需要物理验证的材料不能直接套用。

**易错点：** 漏说同时点火和两端点火；把“每根单端一小时”夸成现实材料一定遵守双端减半。

**题意与证明来源：** 用户截图提供的题意，原帖 URL 与面试日期未核；以上条件说明和证明由整理者独立编写，不是企业标准答案，也未声称做过燃烧实验。

## 可复现检查

在安装 JDK 的机器上，从仓库根目录执行：

```bash
python3 -m unittest discover -s tests -p 'test_interview_algorithms.py' -v
```

该检查先验证文中代码和 Java 文件的示例块一致，再用临时目录编译和运行 Java，构建产物不会写入仓库。没有 java/javac 时运行检查会明确 skip Java 执行，而不是报“已通过算法测试”。也可直接：

```bash
mkdir -p /tmp/interview-algorithms-classes
javac -d /tmp/interview-algorithms-classes tests/java/InterviewAlgorithms.java
java -cp /tmp/interview-algorithms-classes InterviewAlgorithms
```

2026-11-02 已使用临时官方 Temurin JDK 21.0.13+9 编译运行上述测试，发行包已核对 SHA-256；Python 两项检查通过，Java 输出 `PASS: 61162 algorithm checks`。覆盖示例块与执行源码一致、随机/枚举对照、极端整数、缺失 LCA、10 万节点链和 4 万格路径。以上是有限边界与独立对照，不是复杂度证明、并发测试、Android 构建或在线评测认证。JDK 与构建产物不提交到仓库。
