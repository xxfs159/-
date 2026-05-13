from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

from .analysis import course_summary, generate_next_week_plan, identify_weak_points, learning_habit_summary, weekly_review


def _table_to_markdown(df: pd.DataFrame, max_rows: int = 8) -> str:
    if df.empty:
        return "暂无数据"
    return df.head(max_rows).to_markdown(index=False)


def build_report_context(data: Dict[str, pd.DataFrame]) -> Dict[str, object]:
    """把分析结果整理为大模型或规则模板可用的上下文。"""
    return {
        "course_summary": course_summary(data),
        "weak_points": identify_weak_points(data, top_n=5),
        "weekly": weekly_review(data),
        "habit": learning_habit_summary(data),
        "plan": generate_next_week_plan(data),
    }


def generate_rule_based_report(data: Dict[str, pd.DataFrame]) -> str:
    """没有 API Key 时的本地周报生成逻辑。"""
    ctx = build_report_context(data)
    weekly = ctx["weekly"]
    habit = ctx["habit"]
    weak = ctx["weak_points"]
    course_df = ctx["course_summary"]
    plan = ctx["plan"]

    weak_lines = []
    for _, row in weak.iterrows():
        weak_lines.append(
            f"- **{row['course_name']} / {row['knowledge_point']}**：正确率 {row['accuracy']:.0%}，"
            f"错题 {int(row['wrong_count'])} 道，主要错因：{row['main_wrong_reason']}。"
        )
    if not weak_lines:
        weak_lines.append("- 暂无薄弱点数据，请先录入刷题记录。")

    plan_lines = []
    for item in plan:
        plan_lines.append(f"- **{item['day']}｜{item['course']}**：{item['task']} 原因：{item['reason']}")

    lowest_course = None
    if not course_df.empty:
        lowest_course = course_df.sort_values(["accuracy", "avg_score"]).iloc[0]["course_name"]

    report = f"""
# 个人学习档案 AI 助理：周度学习复盘报告

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 一、本周学习概况

- 统计周期：{weekly['week_start']} 至 {weekly['week_end']}
- 学习总时长：**{weekly['study_hours']} 小时**
- 刷题数量：**{weekly['total_problems']} 道**
- 本周刷题正确率：**{weekly['accuracy']:.0%}**
- 平均专注度：**{weekly['avg_focus']} / 5**

整体来看，你本周已经形成了一定的学习记录闭环。系统根据课程成绩、刷题记录、学习时长和笔记情况进行了综合分析。当前最需要优先关注的课程是 **{lowest_course or '暂无'}**，建议下周把复习重心放在低正确率知识点上。

## 二、薄弱知识点诊断

{chr(10).join(weak_lines)}

## 三、学习习惯分析

- 有学习记录的天数：**{habit['active_days']} 天**
- 平均单次学习时长：**{habit['avg_session_minutes']} 分钟**
- 平均专注度：**{habit['avg_focus']} / 5**
- 系统建议：{habit['suggestion']}

## 四、下周个性化学习计划

{chr(10).join(plan_lines)}

## 五、复盘建议

1. 每次刷题后立刻记录错因，不只记录“错了”，还要写清楚为什么错。
2. 对正确率低于 70% 的知识点，不建议继续盲目刷题，应先回到笔记和例题。
3. 每周日生成一次复盘报告，把“计划—执行—反馈—再计划”形成闭环。
4. 课堂笔记应与错题关联，后续可以扩展为 RAG 知识库问答。
"""
    return report.strip()


class DeepSeekReportGenerator:
    """DeepSeek 周报生成器。若未配置 API Key，会自动回退到规则模板。"""

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/chat/completions").strip()
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

    def available(self) -> bool:
        return bool(self.api_key)

    def generate(self, data: Dict[str, pd.DataFrame]) -> str:
        if not self.available():
            return generate_rule_based_report(data)

        ctx = build_report_context(data)
        prompt = f"""
你是一个学习复盘助手。请根据以下数据生成中文周度学习复盘报告。
要求：
1. 结构包括：本周概况、成绩与刷题分析、薄弱知识点、学习习惯问题、下周计划。
2. 语气积极、具体，适合大学生阅读。
3. 不要编造数据，所有判断必须来自给定数据。
4. 输出 Markdown。

课程概况：
{_table_to_markdown(ctx['course_summary'])}

薄弱知识点：
{_table_to_markdown(ctx['weak_points'])}

本周指标：
{ctx['weekly']}

学习习惯：
{ctx['habit']}

下周计划：
{ctx['plan']}
"""
        try:
            resp = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个严谨、温和、擅长学习诊断的 AI 学习助理。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.5,
                },
                timeout=30,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return content.strip()
        except Exception as exc:
            fallback = generate_rule_based_report(data)
            return f"{fallback}\n\n> 注：DeepSeek API 调用失败，已使用本地规则模板生成。错误信息：{exc}"
