from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import List

from .sandbox import RunSummary


@dataclass
class Finding:
    severity: str
    title: str
    detail: str
    suggestion: str


def static_analyze(language: str, code: str) -> List[Finding]:
    language = language.lower().strip()
    findings: List[Finding] = []
    if language in {"python", "py", "python3"}:
        findings.extend(_analyze_python(code))
    elif language in {"c++", "cpp", "cxx"}:
        findings.extend(_analyze_cpp(code))
    else:
        findings.append(Finding("warning", "语言暂未深度支持", "当前只对 Python / C++ 做静态检查。", "切换语言或扩展 analyzer.py。"))
    return findings


def _analyze_python(code: str) -> List[Finding]:
    findings: List[Finding] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [Finding("error", "Python 语法错误", f"第 {e.lineno} 行附近：{e.msg}", "先修正语法，再运行样例测试。")]

    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
            if getattr(node.iter.func, "id", "") == "range" and len(node.iter.args) == 1:
                findings.append(Finding("info", "检查 range 边界", "代码中出现 range(n)，请确认是否需要包含 n 或从 1 开始。", "用样例覆盖最小值、最大值、边界值。"))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            findings.append(Finding("warning", "可能存在浮点除法", "Python 中 / 返回浮点数，OJ 题经常需要整数除法。", "需要整除时使用 //，需要精度时保留 /。"))
    return findings


def _analyze_cpp(code: str) -> List[Finding]:
    findings: List[Finding] = []
    if code.count("{") != code.count("}"):
        findings.append(Finding("error", "大括号数量不匹配", "{ 与 } 的数量不同，可能导致编译失败或结构错乱。", "用编辑器格式化代码，逐层检查函数和循环边界。"))
    if re.search(r"int\s+main\s*\([^)]*\)\s*{", code) and not re.search(r"return\s+0\s*;", code):
        findings.append(Finding("info", "main 函数未显式 return 0", "C++ 中 main 可省略 return 0，但教学项目里建议写清楚。", "在 main 末尾加入 return 0; 增强规范性。"))
    if re.search(r"for\s*\([^;]*<=\s*[^;]*\.size\s*\(\)", code):
        findings.append(Finding("warning", "疑似 vector/string 越界", "循环条件中出现 <= size()，常见错误是访问 a[size()]。", "大多数情况下应使用 i < a.size()。"))
    if re.search(r"cin\s*>>", code) and not re.search(r"ios::sync_with_stdio\s*\(\s*false\s*\)", code):
        findings.append(Finding("info", "可优化输入输出速度", "大量输入时 cin/cout 可能慢。", "在 main 开头加入 ios::sync_with_stdio(false); cin.tie(nullptr);。"))
    if re.search(r"\bint\b", code) and re.search(r"\*|1e9|1000000000|long long", code) is None:
        findings.append(Finding("info", "检查整数范围", "代码大量使用 int，若题目数据范围大可能溢出。", "根据题目范围考虑 long long。"))
    if re.search(r"/\s*2", code) and not re.search(r"long long|double", code):
        findings.append(Finding("info", "检查整除取整", "C++ 整数除法会向 0 取整，可能影响平均数/二分/期望类题。", "确认题目是否需要浮点或向上取整。"))
    return findings


def dynamic_analyze(summary: RunSummary) -> List[Finding]:
    findings: List[Finding] = []
    if not summary.compile_ok:
        findings.append(Finding("error", "编译失败", summary.compile_log.strip()[:1000], "先根据编译器报错定位行号，再重新运行样例。"))
        return findings
    if not summary.results:
        findings.append(Finding("warning", "没有运行测试", "没有可用样例，无法验证结果。", "至少准备 3 类样例：普通、边界、极端。"))
        return findings
    failed = [r for r in summary.results if not r.passed]
    if not failed:
        findings.append(Finding("success", "样例全部通过", f"{summary.passed_count}/{summary.total_count} 个样例通过。", "继续补充边界样例，避免只过样例不过隐藏测试。"))
    else:
        findings.append(Finding("error", "存在未通过样例", f"{len(failed)}/{summary.total_count} 个样例失败。", "优先看第一个失败样例，对比预期输出和实际输出。"))
        if any(r.timed_out for r in failed):
            findings.append(Finding("warning", "可能存在死循环或复杂度过高", "有样例运行超时。", "检查循环终止条件，或优化算法复杂度。"))
        if any(r.returncode != 0 and not r.timed_out for r in failed):
            findings.append(Finding("warning", "运行时错误", "程序出现非 0 返回码，可能是数组越界、除零、断言失败等。", "用最小失败样例复现，再加打印或调试器定位。"))
    return findings
