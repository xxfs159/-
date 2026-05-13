# 个人学习档案 AI 助理

本项目对应《人工智能引论》大项目 **项目1：个人学习档案 AI 助理**。系统目标是构建一个自动化、个性化、可持续更新的学习复盘助手，能够聚合课程成绩、刷题记录、学习笔记和学习时长，自动生成周度学习复盘报告，诊断薄弱知识点与学习习惯问题，并支持自然语言查询个人学习情况。

## 1. 项目功能

| 模块 | 功能说明 |
|---|---|
| 数据采集模块 | 支持录入课程、刷题记录、学习笔记、学习时长 |
| 数据存储模块 | 使用 SQLite 建立个人学习档案数据库 |
| 数据分析模块 | 统计课程成绩、刷题正确率、学习时长趋势，识别薄弱知识点 |
| AI 报告生成模块 | 支持 DeepSeek API 生成周报；无 API Key 时自动使用本地规则模板 |
| 交互展示模块 | 使用 Streamlit 实现可视化看板、数据录入、AI 周报和聊天式查询 |

## 2. 技术栈

- Python 3.10+
- Streamlit：Web 交互界面
- SQLite：轻量级本地数据库
- Pandas：数据分析
- Plotly：可视化图表
- DeepSeek API：周报生成与自然语言问答，可选

## 3. 项目结构

```text
personal_study_ai_assistant_project/
├── app.py                         # Streamlit 主程序
├── requirements.txt               # 依赖列表
├── .env.example                   # DeepSeek 配置示例
├── data/
│   ├── sample_scores.csv
│   ├── sample_problem_records.csv
│   └── sample_study_sessions.csv
├── src/
│   ├── database.py                # SQLite 建表与写入函数
│   ├── seed_data.py               # 生成演示数据
│   ├── analysis.py                # 数据分析、薄弱点识别、计划生成
│   ├── report_generator.py        # DeepSeek / 本地规则周报生成
│   └── chatbot.py                 # 自然语言查询模块
├── docs/
│   ├── 项目报告.md
│   ├── 海报文案.md
│   ├── 答辩讲稿.md
│   └── 提交清单.md
└── tests/
    └── test_analysis.py
```

## 4. 快速运行

### 第一步：创建虚拟环境

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

macOS / Linux：

```bash
source .venv/bin/activate
```

### 第二步：安装依赖

```bash
pip install -r requirements.txt
```

### 第三步：启动系统

```bash
streamlit run app.py
```

启动后浏览器会打开本地页面。系统首次启动会自动生成一份演示学习档案数据库。

## 5. 配置 DeepSeek（可选）

系统不配置 API Key 也能运行。如果希望使用 DeepSeek 生成更自然的周报和问答：

1. 复制 `.env.example` 为 `.env`
2. 填入自己的 `DEEPSEEK_API_KEY`
3. 重新启动 `streamlit run app.py`

`.env` 示例：

```text
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-chat
```

## 6. 演示建议

现场展示可以按以下顺序：

1. 打开学习画像看板，展示课程正确率、学习时长趋势、薄弱点 Top 5。
2. 在“数据录入”中新增一条错题记录，说明系统可以持续更新个人档案。
3. 点击“生成本周 AI 复盘报告”，展示自动生成 Markdown 周报。
4. 在聊天框提问：“我下周应该重点学什么？”展示自然语言查询能力。
5. 解释薄弱点识别算法：正确率、错题数、题目难度、笔记数量共同决定薄弱分。

## 7. 创新点

1. 将分散的学习数据统一建模为“个人学习档案”。
2. 薄弱点识别采用可解释评分，而不是只靠主观判断。
3. 报告生成支持大模型和规则模板双模式，保证可演示、可复现。
4. 形成“记录—分析—诊断—计划—复盘”的闭环学习流程。

## 8. 后续可扩展方向

- 导入学校课程成绩或学习通数据。
- 接入刷题平台 API 自动同步错题。
- 将笔记向量化，扩展为个人 RAG 知识库。
- 加入学习提醒、日历同步和移动端小程序。
