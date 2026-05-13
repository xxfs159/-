from __future__ import annotations

import os
from typing import List

import requests

from .analyzer import Finding
from .sandbox import RunSummary
from .variants import generate_variants, guess_tags


def findings_to_markdown(findings: List[Finding]) -> str:
    icon = {"success": "✅", "info": "ℹ️", "warning": "⚠️", "error": "❌"}
    lines = []
    for f in findings:
        lines.append(f"- {icon.get(f.severity, '•')} **{f.title}**：{f.detail}  ")
        lines.append(f"  - 建议：{f.suggestion}")
    return "\n".join(lines)


def results_to_markdown(summary: RunSummary) -> str:
    if not summary.compile_ok:
        return f"### 编译结果\n```text\n{summary.compile_log}\n```"
    if not summary.results:
        return "### 测试结果\n没有测试用例。"
    lines = ["### 测试结果", "| 样例 | 是否通过 | 期望输出 | 实际输出 | 备注 |", "|---|---:|---|---|---|"]
    for r in summary.results:
        passed = "✅" if r.passed else "❌"
        note = "超时" if r.timed_out else ("运行时错误" if r.returncode != 0 else "")
        exp = r.expected.replace("\n", "\\n")[:80]
        out = r.stdout.replace("\n", "\\n")[:80]
        lines.append(f"| {r.name} | {passed} | `{exp}` | `{out}` | {note} |")
    return "\n".join(lines)


def build_local_report(problem: str, language: str, code: str, summary: RunSummary, findings: List[Finding]) -> str:
    tags = ", ".join(guess_tags(problem, code))
    pass_info = f"{summary.passed_count}/{summary.total_count}" if summary.compile_ok else "编译失败"
    return f"""# CodeCoach-AI 诊断报告

## 1. 题目与标签
- 语言：{language}
- 识别标签：{tags}
- 样例通过情况：{pass_info}

## 2. 自动诊断
{findings_to_markdown(findings)}

{results_to_markdown(summary)}

## 3. 下一步修复顺序
1. 先解决编译错误或运行时错误。
2. 若能运行但答案错误，优先分析第一个失败样例。
3. 增加边界测试：最小输入、最大输入、重复值、特殊值。
4. 修复后重新运行全部样例，并记录错误原因。

## 4. 变式训练
{generate_variants(problem, code)}
"""


def maybe_llm_enhance(problem: str, language: str, code: str, local_report: str) -> str:
    """Use DeepSeek API when DEEPSEEK_API_KEY is available; otherwise return local report."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return local_report + "\n\n> 提示：当前未配置 DEEPSEEK_API_KEY，因此使用本地规则版报告。配置后可生成更自然的讲解。"

    prompt = f"""你是一个大学编程课 AI 助教。请基于本地诊断报告，输出更清晰的 Markdown 讲解：
- 先指出最可能的错误位置和原因
- 再给修复思路，不要直接只甩代码
- 最后给 1 道变式题

题目：
{problem}

语言：{language}

代码：
```{language}
{code}
```

本地诊断报告：
{local_report}
"""
    try:
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是严谨、耐心、适合大学新生的编程助教。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:  # keep demo robust
        return local_report + f"\n\n> LLM 增强失败，已回退到本地报告：{e}"
