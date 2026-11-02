import java.math.BigInteger;
import java.util.*;
import java.util.concurrent.ThreadLocalRandom;

/** Standalone, dependency-free examples for the 2026-11-02 algorithm guide. */
public final class InterviewAlgorithms {
    // BEGIN quicksort
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
    // END quicksort

    // BEGIN smallest-k
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
    // END smallest-k

    // BEGIN coin-change
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
    // END coin-change

    // BEGIN lca
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
    // END lca

    // BEGIN increasing-path
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
    // END increasing-path

    private static int checks;
    private static void check(boolean condition, String label) {
        checks++;
        if (!condition) throw new AssertionError(label);
    }
    private static void throwsIllegal(Runnable action, String label) {
        try { action.run(); throw new AssertionError(label); }
        catch (IllegalArgumentException expected) { checks++; }
    }

    private static BigInteger coinOracle(int[] coins, int index, int remaining) {
        if (index == coins.length) return remaining == 0 ? BigInteger.ONE : BigInteger.ZERO;
        BigInteger count = BigInteger.ZERO;
        for (int used = 0; used <= remaining; used += coins[index]) {
            count = count.add(coinOracle(coins, index + 1, remaining - used));
        }
        return count;
    }

    private static int pathOracle(int[][] grid, int r, int c) {
        int best = 1;
        for (int[] d : DIRECTIONS) {
            int nr = r + d[0], nc = c + d[1];
            if (inside(nr, nc, grid.length, grid[0].length) && grid[nr][nc] > grid[r][c])
                best = Math.max(best, 1 + pathOracle(grid, nr, nc));
        }
        return best;
    }

    public static void main(String[] args) {
        Random random = new Random(20261102L);
        int[][] fixedArrays = {{}, {1}, {2, 1}, {1, 1, 1},
                {Integer.MAX_VALUE, 0, Integer.MIN_VALUE, Integer.MAX_VALUE}};
        for (int[] input : fixedArrays) {
            int[] expected = input.clone(), actual = input.clone();
            Arrays.sort(expected); quickSort(actual);
            check(Arrays.equals(actual, expected), "fixed quicksort");
        }
        for (int t = 0; t < 500; t++) {
            int[] input = new int[random.nextInt(120)];
            for (int i = 0; i < input.length; i++) input[i] = random.nextInt(17) - 8;
            int[] original = input.clone(), expected = input.clone(), actual = input.clone();
            Arrays.sort(expected); quickSort(actual);
            check(Arrays.equals(actual, expected), "random quicksort");
            for (int k = 0; k <= input.length; k++) {
                check(Arrays.equals(smallestKSorted(input, k), Arrays.copyOf(expected, k)), "smallest k");
                if (k != 0) check(kthLargest(input, k) == expected[input.length - k], "kth largest");
            }
            check(Arrays.equals(input, original), "selection leaves input unchanged");
        }
        int[] longSorted = new int[50_000];
        for (int i = 0; i < longSorted.length; i++) longSorted[i] = i;
        quickSort(longSorted);
        check(longSorted[49_999] == 49_999, "long sorted array");
        Arrays.fill(longSorted, 7); quickSort(longSorted);
        check(longSorted[0] == 7 && longSorted[49_999] == 7, "all equal array");
        int[] extremes = {Integer.MIN_VALUE, Integer.MAX_VALUE, 0};
        check(Arrays.equals(smallestKSorted(extremes, 2), new int[]{Integer.MIN_VALUE, 0}), "safe comparator");
        throwsIllegal(() -> smallestKSorted(new int[]{1}, -1), "negative k");
        throwsIllegal(() -> smallestKSorted(new int[]{1}, 2), "oversized k");
        throwsIllegal(() -> kthLargest(new int[]{1}, 0), "zero rank");
        throwsIllegal(() -> kthLargest(new int[0], 1), "empty rank");

        check(countChange(5, new int[]{1, 2, 5}).equals(BigInteger.valueOf(4)), "coin example");
        check(countChange(0, new int[]{}).equals(BigInteger.ONE), "zero amount");
        check(countChange(3, new int[]{2}).equals(BigInteger.ZERO), "unreachable amount");
        throwsIllegal(() -> countChange(-1, new int[]{1}), "negative amount");
        throwsIllegal(() -> countChange(4, new int[]{0, 1}), "zero coin");
        throwsIllegal(() -> countChange(4, new int[]{-1, 2}), "negative coin");
        throwsIllegal(() -> countChange(4, new int[]{1, 1}), "duplicate coin");
        for (int mask = 0; mask < 32; mask++) {
            int[] coins = new int[Integer.bitCount(mask)];
            int n = 0;
            for (int bit = 0; bit < 5; bit++) if ((mask & (1 << bit)) != 0) coins[n++] = bit + 1;
            for (int amount = 0; amount <= 20; amount++)
                check(countChange(amount, coins).equals(coinOracle(coins, 0, amount)), "coin oracle");
        }
        int[] manyCoins = new int[100];
        for (int i = 0; i < manyCoins.length; i++) manyCoins[i] = i + 1;
        check(countChange(1000, manyCoins).compareTo(BigInteger.valueOf(Long.MAX_VALUE)) > 0, "big integer count");

        TreeNode root = new TreeNode(3), left = new TreeNode(5), right = new TreeNode(1);
        TreeNode a = new TreeNode(6), b = new TreeNode(2), c = new TreeNode(5);
        root.left = left; root.right = right; left.left = a; left.right = b; b.left = c;
        check(lowestCommonAncestor(root, left, right) == root, "LCA split");
        check(lowestCommonAncestor(root, left, c) == left, "LCA ancestor");
        check(lowestCommonAncestor(root, c, c) == c, "LCA identical target");
        check(lowestCommonAncestor(root, c, new TreeNode(5)) == null, "LCA identity and missing");
        check(lowestCommonAncestor(root, null, c) == null, "LCA null target");
        check(lowestCommonAncestor(null, c, c) == null, "LCA empty tree");
        TreeNode chain = new TreeNode(0), cursor = chain, mid = null;
        for (int i = 1; i < 100_000; i++) {
            cursor.right = new TreeNode(i); cursor = cursor.right;
            if (i == 50_000) mid = cursor;
        }
        check(lowestCommonAncestor(chain, mid, cursor) == mid, "LCA deep nonrecursive tree");

        check(longestIncreasingPath(new int[][]{}) == 0, "empty grid");
        check(longestIncreasingPath(new int[][]{{}}) == 0, "zero columns");
        check(longestIncreasingPath(new int[][]{{1}}) == 1, "single cell");
        check(longestIncreasingPath(new int[][]{{9,9,4},{6,6,8},{2,1,1}}) == 4, "matrix example");
        check(longestIncreasingPath(new int[][]{{7,7},{7,7}}) == 1, "equal cells");
        check(longestIncreasingPath(new int[][]{{Integer.MIN_VALUE, 0, Integer.MAX_VALUE}}) == 3, "extreme cells");
        throwsIllegal(() -> longestIncreasingPath(new int[][]{{1}, {1,2}}), "ragged matrix");
        throwsIllegal(() -> longestIncreasingPath(new int[][]{null}), "null row");
        for (int t = 0; t < 200; t++) {
            int[][] grid = new int[1 + random.nextInt(4)][1 + random.nextInt(4)];
            int expected = 0;
            for (int[] row : grid) for (int j = 0; j < row.length; j++) row[j] = random.nextInt(7);
            for (int r = 0; r < grid.length; r++) for (int col = 0; col < grid[0].length; col++)
                expected = Math.max(expected, pathOracle(grid, r, col));
            check(longestIncreasingPath(grid) == expected, "matrix brute-force oracle");
        }
        int[][] longPath = new int[1][40_000];
        for (int i = 0; i < longPath[0].length; i++) longPath[0][i] = i;
        check(longestIncreasingPath(longPath) == 40_000, "matrix nonrecursive long path");
        System.out.println("PASS: " + checks + " algorithm checks");
    }
}
