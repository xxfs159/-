from __future__ import annotations

import re
from typing import List


def guess_tags(problem: str, code: str) -> List[str]:
    text = (problem + "\n" + code).lower()
    tags = []
    rules = [
        ("二分", ["binary", "mid", "二分"]),
        ("动态规划", ["dp", "动态规划", "状态转移"]),
        ("图论", ["graph", "bfs", "dfs", "最短路", "邻接表"]),
        ("字符串", ["string", "字符串", "substr"]),
        ("排序/贪心", ["sort", "greedy", "贪心", "排序"]),
        ("前缀和", ["prefix", "前缀和", "sum["]),
    ]
    for tag, keys in rules:
        if any(k in text for k in keys):
            tags.append(tag)
    return tags or ["基础模拟"]


def generate_variants(problem: str, code: str) -> str:
    tags = guess_tags(problem, code)
    main = tags[0]
    if main == "二分":
        return """### 同类变式训练题：最小可行速度
给定 n 个任务量 a[i] 和总时间 T，要求选择一个最小整数速度 v，使得 sum(ceil(a[i]/v)) <= T。输出最小 v。

**训练目标**：二分答案、上取整、边界处理。  
**提示**：判断函数 check(v) 是否可行；左边界为 1，右边界为 max(a)。"""
    if main == "动态规划":
        return """### 同类变式训练题：限制次数的最大收益
给定 n 天价格，最多进行 k 次买卖，求最大收益。

**训练目标**：状态定义、转移方程、初始化。  
**提示**：dp[i][j][0/1] 表示第 i 天、完成 j 次交易、是否持有股票。"""
    if main == "图论":
        return """### 同类变式训练题：迷宫最短步数
给定 n*m 网格，0 表示可走，1 表示障碍，从左上角走到右下角，输出最短步数，不可达输出 -1。

**训练目标**：BFS、队列、visited 数组。"""
    if main == "字符串":
        return """### 同类变式训练题：最长无重复子串
给定一个字符串，求不含重复字符的最长连续子串长度。

**训练目标**：双指针、哈希表、边界更新。"""
    return """### 同类变式训练题：区间最大和
给定长度为 n 的整数数组，求连续子数组的最大和。

**训练目标**：基础模拟到动态规划的过渡、边界初始化。  
**提示**：维护当前连续和 cur 与答案 ans。"""
