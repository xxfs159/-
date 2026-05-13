from __future__ import annotations

import gradio as gr

from codecoach_ai.analyzer import dynamic_analyze, static_analyze
from codecoach_ai.parser import parse_test_cases
from codecoach_ai.reporter import build_local_report, maybe_llm_enhance
from codecoach_ai.sandbox import run_solution

DEFAULT_PROBLEM = """输入两个整数 a, b，输出它们的和。"""

DEFAULT_CODE = """#include <bits/stdc++.h>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a - b << endl; // 故意写错：应为 a + b
    return 0;
}
"""

DEFAULT_TESTS = """1 2
---
3
===
10 5
---
15
"""


def diagnose(problem: str, language: str, code: str, tests: str, use_llm: bool):
    try:
        cases = parse_test_cases(tests)
    except Exception as e:
        return f"## 测试用例解析失败\n{e}"

    summary = run_solution(language, code, cases)
    findings = static_analyze(language, code) + dynamic_analyze(summary)
    local_report = build_local_report(problem, language, code, summary, findings)
    if use_llm:
        return maybe_llm_enhance(problem, language, code, local_report)
    return local_report


with gr.Blocks(title="CodeCoach-AI 编程错解诊断机器人") as demo:
    gr.Markdown("# CodeCoach-AI：编程题错解诊断与变式训练系统")
    gr.Markdown("输入题目、错解代码和样例，系统会自动编译/运行、定位可疑问题，并生成 Markdown 诊断报告。")

    with gr.Row():
        with gr.Column(scale=1):
            problem = gr.Textbox(label="题目描述", value=DEFAULT_PROBLEM, lines=6)
            language = gr.Dropdown(label="语言", choices=["C++", "Python"], value="C++")
            tests = gr.Textbox(label="测试用例", value=DEFAULT_TESTS, lines=8, info="用 --- 分隔输入/期望输出，用 === 分隔多个样例；也支持 JSON 数组。")
            use_llm = gr.Checkbox(label="使用 DeepSeek 增强讲解（需配置 DEEPSEEK_API_KEY）", value=False)
        with gr.Column(scale=1):
            code = gr.Code(label="错解代码", value=DEFAULT_CODE, language="cpp", lines=18)

    btn = gr.Button("开始诊断", variant="primary")
    report = gr.Markdown(label="诊断报告")
    btn.click(diagnose, inputs=[problem, language, code, tests, use_llm], outputs=report)


if __name__ == "__main__":
    demo.launch()
