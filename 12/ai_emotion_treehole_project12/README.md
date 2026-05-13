# 项目12：AI 陪聊情绪树洞 —— 情绪识别与心理资源转介助手

## 1. 项目简介

本项目是一个面向大学生和年轻用户的情绪陪伴类 Web Demo。用户可以匿名输入烦恼、压力或日常心情，系统会自动识别主要情绪类型，并生成温和、共情、非评判的陪伴式回应。同时，系统会保存每日情绪记录，形成情绪趋势图；当输入中出现自伤、自杀、极端绝望等高风险表达时，系统会触发危机词报警，并提示联系现实支持资源。

> 注意：本项目是课程演示型系统，不能替代医生、心理咨询师或学校心理中心的专业服务。

## 2. 对应课程要求

PPT 中项目12要求包括：匿名情绪树洞、情绪识别、陪伴式回应、情绪记录、自我照护建议和危机词报警。本项目逐项实现这些功能，并补充了可视化趋势、SQLite 本地存储、DeepSeek API 可选增强模式和答辩材料。

## 3. 技术栈

- 前端/界面：Streamlit
- 数据处理：Pandas
- 可视化：Plotly
- 本地数据存储：SQLite
- 情绪识别：关键词词典 + 可解释规则
- 回复生成：本地安全模板；可选 DeepSeek API
- 危机检测：高风险关键词匹配 + 资源转介提示

## 4. 项目结构

```text
ai_emotion_treehole_project12/
├── app.py                         # Streamlit 主程序
├── requirements.txt               # 依赖列表
├── run_app.bat                    # Windows 一键运行脚本
├── run_app.sh                     # macOS/Linux 一键运行脚本
├── ai_emotion_treehole/
│   ├── emotion_core.py            # 情绪识别核心逻辑
│   ├── response_generator.py      # 陪伴式回应生成
│   ├── crisis.py                  # 危机词检测与安全回应
│   └── storage.py                 # SQLite 存储
├── data/
│   ├── emotion_lexicon.json       # 情绪词典
│   ├── crisis_keywords.json       # 危机词词表
│   ├── resources.json             # 心理支持资源
│   └── sample_inputs.json         # 示例输入
├── docs/
│   ├── 项目报告.md
│   ├── PPT大纲.md
│   ├── 海报内容.md
│   ├── 答辩讲稿.md
│   ├── 测试说明.md
│   └── 提交清单.md
└── tests/
    └── test_core.py               # 简单单元测试
```

## 5. 快速运行

### 方法一：命令行运行

```bash
cd ai_emotion_treehole_project12
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开提示的本地地址，一般是：

```text
http://localhost:8501
```

### 方法二：Windows 一键运行

双击 `run_app.bat`。

### 方法三：macOS / Linux 一键运行

```bash
chmod +x run_app.sh
./run_app.sh
```

## 6. 可选：接入 DeepSeek API

不配置 API Key 时，系统会使用本地模板生成回应，保证一定能跑。若希望展示大模型生成效果，可以设置环境变量：

```bash
export DEEPSEEK_API_KEY="你的API Key"
streamlit run app.py
```

Windows PowerShell：

```powershell
$env:DEEPSEEK_API_KEY="你的API Key"
streamlit run app.py
```

## 7. 核心功能演示

1. 在“情绪树洞”页输入一段心情，例如：

```text
最近期末考试和项目DDL挤在一起，我总觉得来不及，晚上睡不着。
```

2. 系统输出：
   - 主要情绪：焦虑/压力
   - 置信度
   - 识别原因
   - 陪伴式回应
   - 自我照护建议

3. 在“情绪趋势”页查看：
   - 情绪类型分布柱状图
   - 置信度变化折线图
   - 历史记录表格
   - CSV 导出

4. 输入高风险文本时，系统会显示危机提醒和资源转介提示。

## 8. 设计亮点

- **可解释情绪识别**：不用黑盒模型也能展示“为什么判断为某类情绪”。
- **安全优先**：把危机表达与普通情绪倾诉分流处理。
- **本地可运行**：无 API 也可演示，避免现场网络或额度问题。
- **可扩展性强**：后续可替换为 BERT 情感分类器、接入 RAG 心理资源库或加入多轮对话记忆。

## 9. 后续改进方向

- 使用人工标注的大学生情绪语料微调分类模型。
- 加入多轮对话状态管理，避免每次只看单句。
- 将心理资源从 JSON 升级为 RAG 知识库。
- 增加隐私保护，如本地加密、自动脱敏和定期删除。
- 加入专业审核机制，避免 AI 生成不合适建议。

## 10. 提交建议

建议提交以下内容：

- 源代码压缩包
- README
- 项目报告
- PPT 或海报
- 运行演示截图/录屏
- 现场可运行 Demo
