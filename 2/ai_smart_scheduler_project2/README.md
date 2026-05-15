# AI 智能课表与学习计划生成系统（项目2）

本项目对应《人工智能引论大项目》中的**项目2：AI 智能课表与学习计划生成系统**。系统面向大学生日常学习管理场景，支持导入课程表、任务 DDL、空闲时间，并根据任务优先级和时间约束自动生成一周学习计划。

## 1. 项目亮点

1. **自然语言任务解析**  
   用户可以输入“下周三 23:59 AI大项目报告截止，预计6小时，很重要”等自然语言，系统自动识别截止时间、预计耗时、优先级和任务类型。

2. **规划型 Agent 思路**  
   系统把“任务 DDL、课程占用、个人空闲时段、任务优先级”统一建模，通过调度算法生成可执行计划。

3. **可解释的学习计划**  
   每个计划块都展示开始时间、结束时间、任务名称、课程归属、优先级和 DDL，便于用户理解系统为什么这样安排。

4. **可选大模型总结**  
   如果配置 DeepSeek API Key，系统可以调用大模型生成学习建议；如果不配置，也可以使用本地模板总结，保证演示稳定。

## 2. 技术栈

- Python 3.10+
- Streamlit：Web 交互界面
- Pandas：CSV 数据处理
- 正则表达式 NLP：中文时间、耗时、优先级解析
- 规则规划 Agent：任务排序、时间槽分配、冲突规避
- DeepSeek API（可选）：生成学习建议和复盘文字

## 3. 项目结构

```text
ai_smart_scheduler_project2/
├── app.py                         # Streamlit 主程序
├── requirements.txt               # Python 依赖
├── data/
│   ├── sample_courses.csv         # 示例课程表
│   ├── sample_tasks.csv           # 示例任务/DDL
│   └── sample_free_slots.csv      # 示例空闲时间
├── src/
│   ├── models.py                  # 数据模型
│   ├── nlp_parser.py              # 自然语言解析
│   ├── planner.py                 # 规划算法核心
│   ├── deepseek_client.py         # 可选大模型调用
│   ├── feishu_mcp_mock.py         # 飞书 MCP 同步模拟 JSON
│   └── utils.py                   # 工具函数
├── docs/
│   ├── 项目报告.md
│   ├── 汇报PPT大纲.md
│   ├── 海报易拉宝文案.md
│   ├── 答辩问题与回答.md
│   └── 提交清单.md
└── tests/
    └── test_planner.py
```

## 4. 安装与运行

### 第一步：进入项目目录

```bash
cd ai_smart_scheduler_project2
```

### 第二步：安装依赖

```bash
pip install -r requirements.txt
```

### 第三步：启动系统

```bash
streamlit run app.py
```

浏览器打开后即可看到系统界面。

## 5. 输入数据格式

### 课程表 `data/sample_courses.csv`

| 字段 | 含义 |
|---|---|
| weekday | 星期，0表示周一，6表示周日 |
| course_name | 课程名称 |
| start_time | 上课开始时间 |
| end_time | 上课结束时间 |
| location | 地点 |
| teacher | 教师 |

### 任务表 `data/sample_tasks.csv`

| 字段 | 含义 |
|---|---|
| task_name | 任务名称 |
| course | 所属课程 |
| deadline | 截止时间 |
| estimated_hours | 预计耗时 |
| priority | 优先级，1-5 |
| task_type | 作业/复习/项目/展示 |
| description | 任务说明 |

### 空闲时间 `data/sample_free_slots.csv`

| 字段 | 含义 |
|---|---|
| weekday | 星期，0表示周一，6表示周日 |
| start_time | 空闲开始时间 |
| end_time | 空闲结束时间 |
| energy_level | 精力水平，可填 high/medium/low |

## 6. 自然语言输入示例

```text
人工智能：下周三 23:59 AI大项目报告 截止，预计6小时，很重要
高数：5月20日 20:00 章节复习 需要3小时
英语：周五 18:00 口语展示准备 预计2小时
```

系统会自动解析为结构化任务。

## 7. 可选 DeepSeek 配置

不配置 API Key 也能正常运行。如果想启用大模型总结：

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="你的key"

# macOS/Linux
export DEEPSEEK_API_KEY="你的key"
```

如接口地址或模型名变化，可设置：

```bash
export DEEPSEEK_BASE_URL="你的接口地址"
export DEEPSEEK_MODEL="你的模型名"
```

## 8. 飞书 MCP 协作能力说明

课程演示版不直接调用真实飞书账号，避免 token 配置和网络环境影响现场展示。系统在“导出与总结”页面提供“飞书 MCP 同步模拟 JSON”，可把每个学习计划块转换为日历事件 payload。后续接入真实飞书 MCP 时，只需要把该 JSON 交给 MCP 工具创建日程或任务即可。

## 9. 提交建议

建议提交以下内容：

- 项目代码压缩包
- 运行截图
- `docs/项目报告.md`
- `docs/汇报PPT大纲.md`
- 海报或易拉宝设计稿
- 现场演示视频或现场运行系统

## 10. 可扩展方向

- 接入飞书/钉钉日历，实现任务同步和消息提醒。
- 用更强的中文时间解析库提升解析准确率。
- 加入用户习惯学习，根据历史完成情况动态调整计划。
- 加入番茄钟和完成打卡，形成闭环学习管理。
