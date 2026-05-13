# 智能简历优化与岗位推荐平台

本项目对应《人工智能引论》大项目 **项目5：智能简历优化与岗位推荐平台**。系统通过简历解析、岗位 JD 知识库、向量检索匹配、规则增强评分与生成式文本优化，实现“上传简历 → 匹配岗位 → 输出简历优化建议 → 生成求职信与面试要点”的求职辅助流程。

## 1. 项目亮点

1. **RAG 岗位知识库匹配**：将岗位 JD、技能要求、岗位职责等信息向量化，检索最适合用户简历的岗位。
2. **可解释匹配评分**：不仅给出岗位推荐结果，还展示匹配技能、缺失技能、推荐理由和提升建议。
3. **简历内容优化生成**：根据目标岗位自动生成简历摘要、项目经历优化建议、求职信和面试准备要点。
4. **DeepSeek 可选接入**：默认可离线运行；配置 `DEEPSEEK_API_KEY` 后可调用 DeepSeek API 生成更自然的文本。

## 2. 技术栈

- 前端/交互：Streamlit
- 数据处理：Pandas、NumPy
- NLP/检索：TF-IDF 字符 n-gram 向量化、余弦相似度、技能关键词抽取
- RAG 思路：岗位 JD 作为知识库，用户简历作为 Query，检索 Top-K 相关岗位
- 生成模块：本地模板生成 + DeepSeek API 可选增强
- 支持文件：TXT、PDF、DOCX 简历上传

> 说明：课程要求中提到 BGE embedding 和 DeepSeek。为方便课堂演示与复现，本项目默认使用无需模型下载的 TF-IDF 方案模拟向量检索流程；如需增强，可将 `src/rag_matcher.py` 中的向量化模块替换为 BGE embedding。

## 3. 目录结构

```text
resume_job_ai_platform/
├── app.py                         # Streamlit 主程序
├── requirements.txt               # 依赖列表
├── README.md                      # 项目说明
├── data/
│   └── jobs.csv                   # 示例岗位 JD 知识库
├── samples/
│   └── resume_example.txt         # 示例简历
├── src/
│   ├── __init__.py
│   ├── resume_parser.py           # 简历文本解析与技能抽取
│   ├── rag_matcher.py             # RAG 检索与岗位匹配评分
│   ├── generator.py               # 简历优化、求职信、面试要点生成
│   └── utils.py                   # 通用工具函数
├── docs/
│   ├── report.md                  # 课程项目报告
│   ├── poster_text.md             # 海报/易拉宝文案
│   ├── presentation_script.md     # 现场汇报稿
│   └── defense_qa.md              # 答辩问答准备
└── tests/
    └── test_core.py               # 核心函数测试
```

## 4. 快速运行

### 4.1 创建环境

```bash
cd resume_job_ai_platform
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

### 4.2 安装依赖

```bash
pip install -r requirements.txt
```

### 4.3 启动系统

```bash
streamlit run app.py
```

打开浏览器中的本地地址，一般为：

```text
http://localhost:8501
```

### 4.4 使用方式

1. 在左侧上传简历文件，支持 `.txt`、`.pdf`、`.docx`。
2. 没有简历文件时，可以点击“使用示例简历”。
3. 选择或输入求职方向。
4. 点击“开始智能匹配”。
5. 查看岗位推荐列表、匹配度、缺失技能、简历优化建议、求职信和面试要点。
6. 下载 Markdown 格式的个人求职优化报告。

## 5. 可选：接入 DeepSeek

如果需要调用 DeepSeek 生成更自然的内容，可以设置环境变量：

Windows PowerShell：

```powershell
$env:DEEPSEEK_API_KEY="你的API_KEY"
```

macOS / Linux：

```bash
export DEEPSEEK_API_KEY="你的API_KEY"
```

系统会自动检测该环境变量。没有配置时，将使用本地模板生成，不影响演示。

## 6. 核心流程

```text
上传简历
  ↓
文本抽取与清洗
  ↓
技能/项目/教育/经历信息抽取
  ↓
岗位 JD 知识库向量化
  ↓
用户简历与岗位向量相似度计算
  ↓
技能重合度、方向偏好、经验要求综合评分
  ↓
Top-K 岗位推荐
  ↓
生成简历优化建议、求职信、面试要点
```

## 7. 项目适合作业展示的内容

- 系统演示：上传简历并得到岗位推荐结果
- 算法讲解：RAG 检索、文本向量化、相似度计算、技能匹配
- 可解释性展示：匹配原因、缺失技能、优化建议
- 未来改进：BGE Embedding、真实招聘网站爬虫、DeepSeek 多轮对话优化、用户反馈闭环

## 8. 常见问题

### Q1：为什么默认不用真实招聘网站爬虫？

课程展示更看重技术链路是否完整和可复现。真实招聘网站反爬限制较多，课堂演示不稳定，因此使用 `jobs.csv` 模拟岗位知识库。后续可扩展为爬虫自动更新。

### Q2：为什么不用大型向量模型？

BGE embedding 效果更好，但需要额外下载模型并占用算力。为了让项目在普通电脑上稳定运行，默认采用 TF-IDF 向量化；报告中已说明可替换为 BGE。

### Q3：项目的 AI 体现在哪里？

AI 体现在自然语言处理、简历信息抽取、岗位语义匹配、RAG 检索增强、简历优化生成、求职信与面试要点生成等环节。
