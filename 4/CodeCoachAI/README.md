# CodeCoach-AI：编程题错解诊断与变式训练系统

这是《人工智能引论》大项目的可运行 MVP。系统面向编程学习者，支持输入题目、错解代码和测试样例，自动完成：

1. 静态检查：语法、边界、类型、常见 C++/Python 错误提示。
2. 动态验证：本地编译/运行代码，对比样例输出。
3. 报告生成：输出 Markdown 诊断报告。
4. 变式训练：根据题目/代码标签生成同类练习题。
5. LLM 增强：可选调用 DeepSeek API 生成更自然的讲解。

## 一键运行

```bash
pip install -r requirements.txt
python app.py
```

浏览器打开 Gradio 给出的本地地址即可。

## 使用 DeepSeek 增强讲解

Linux/macOS/WSL:

```bash
export DEEPSEEK_API_KEY="你的 key"
python app.py
```

Windows PowerShell:

```powershell
$env:DEEPSEEK_API_KEY="你的 key"
python app.py
```

不配置 API Key 时，系统会自动使用本地规则版报告。

## 测试用例格式

### 简洁格式

```text
1 2
---
3
===
10 5
---
15
```

### JSON 格式

```json
[
  {"name": "样例1", "input": "1 2\n", "expected": "3\n"},
  {"name": "样例2", "input": "10 5\n", "expected": "15\n"}
]
```

## 项目结构

```text
CodeCoachAI/
├── app.py
├── requirements.txt
├── README.md
├── PROJECT_REPORT.md
├── POSTER_CONTENT.md
├── examples/
│   ├── wrong_sum.cpp
│   └── sample_tests.txt
└── codecoach_ai/
    ├── analyzer.py
    ├── parser.py
    ├── reporter.py
    ├── sandbox.py
    └── variants.py
```

## 展示建议

现场展示时，先运行默认示例：`a+b` 题中代码写成 `a-b`。系统会发现样例失败，并生成诊断报告。然后再换一个带边界错误的 C++ 题，展示静态检查与动态测试的结合。

## 注意

本项目的 sandbox 是教学演示版，不是生产级安全沙箱。正式系统应使用 Docker、资源限制、网络隔离和更严格的权限控制。
