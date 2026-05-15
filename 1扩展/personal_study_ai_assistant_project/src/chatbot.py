from __future__ import annotations

import os
from typing import Dict

import pandas as pd
import requests
from dotenv import load_dotenv

from .analysis import course_summary, generate_next_week_plan, identify_weak_points, learning_habit_summary


def _format_weak_points(weak: pd.DataFrame) -> str:
    if weak.empty:
        return "目前还没有足够的刷题记录来判断薄弱点。"
    lines = ["当前系统识别出的主要薄弱点如下："]
    for _, row in weak.iterrows():
        lines.append(
            f"- {row['course_name']}｜{row['knowledge_point']}：正确率 {row['accuracy']:.0%}，"
            f"错题 {int(row['wrong_count'])} 道，建议先复盘错因“{row['main_wrong_reason']}”。"
        )
    return "\n".join(lines)


def answer_question(question: str, data: Dict[str, pd.DataFrame]) -> str:
    """
    学习档案自然语言问答。
    优先调用 DeepSeek；若没有 API Key，则使用可解释的规则问答。
    """
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if api_key:
        return _answer_with_deepseek(question, data, api_key)

    q = question.strip()
    weak = identify_weak_points(data, top_n=5)
    course_df = course_summary(data)
    habit = learning_habit_summary(data)

    if any(k in q for k in ["薄弱", "弱点", "不会", "差", "错题"]):
        return _format_weak_points(weak)

    if any(k in q for k in ["正确率", "刷题", "做题"]):
        if course_df.empty:
            return "暂无刷题数据。"
        lines = ["各课程刷题表现："]
        for _, row in course_df.iterrows():
            lines.append(
                f"- {row['course_name']}：刷题 {int(row['practice_count'])} 道，正确率 {row['accuracy']:.0%}。"
            )
        return "\n".join(lines)

    if any(k in q for k in ["时长", "学习多久", "专注", "习惯"]):
        return (
            f"当前共有 {habit['active_days']} 天学习记录，平均单次学习 {habit['avg_session_minutes']} 分钟，"
            f"平均专注度 {habit['avg_focus']} / 5。建议：{habit['suggestion']}"
        )

    if any(k in q for k in ["计划", "下周", "安排"]):
        plan = generate_next_week_plan(data)
        return "\n".join([f"- {p['day']}：{p['course']}，{p['task']}" for p in plan])

    return (
        "我可以回答：你的薄弱知识点是什么、各课程正确率如何、学习时长和专注度怎样、下周如何安排。"
        "例如可以问：“我下周应该重点学什么？”"
    )


def _answer_with_deepseek(question: str, data: Dict[str, pd.DataFrame], api_key: str) -> str:
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/chat/completions")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    weak = identify_weak_points(data, top_n=5)
    course_df = course_summary(data)
    habit = learning_habit_summary(data)
    prompt = f"""
用户问题：{question}

请只基于以下学习档案数据回答，不要编造。
课程概况：
{course_df.to_markdown(index=False)}

薄弱知识点：
{weak.to_markdown(index=False)}

学习习惯：
{habit}
"""
    try:
        resp = requests.post(
            base_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是个人学习档案 AI 助理，回答要具体、温和、可执行。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return f"DeepSeek API 调用失败，已无法生成大模型回答。错误：{exc}"
