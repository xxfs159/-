from __future__ import annotations

import os
from typing import Dict, List, Optional

import requests


SYSTEM_SAFETY_RULES = (
    "你是一个课程演示用的情绪陪伴助手，不进行医学诊断，不提供治疗方案。"
    "你的回复应温和、共情、非评判，鼓励用户联系现实中的可信任支持。"
    "当出现自伤、自杀、暴力等危机风险时，只做安全陪伴和转介，要求用户联系紧急服务或身边真人。"
)


def fallback_supportive_reply(text: str, analysis: Dict[str, object], is_crisis: bool = False) -> str:
    """无需 API 的本地回复模板。"""
    emotion = analysis.get("emotion", "平静")
    intensity = analysis.get("intensity", "低")
    suggestions = analysis.get("suggestions", [])

    if is_crisis:
        return (
            "听起来你现在真的很难受，而且可能已经接近危险边缘。"
            "我不会评判你，也不希望你一个人扛着。请先做一件保护自己的事："
            "把可能伤害自己的物品放远，去到有人在的地方，马上联系身边可信任的人。"
            "如果你觉得自己可能马上做出伤害行为，请立即拨打 120/110 或 12356。"
        )

    opening = {
        "焦虑": "我能感觉到你现在像是被很多不确定的事情压住了。",
        "低落": "你描述的状态听起来很消耗，能说出来已经很不容易。",
        "愤怒": "你现在的生气和委屈是可以被理解的，先不用急着否定自己的感受。",
        "孤独": "那种“好像没人懂我”的感觉会让人很难受，我愿意先听你把它说完。",
        "压力": "你面对的任务可能比较密集，压力感是真实存在的。",
        "积极": "听起来今天有一些让你感到被支持或被肯定的时刻。",
        "平静": "谢谢你把此刻的状态写下来，记录本身就是一种照顾自己。",
    }.get(str(emotion), "谢谢你愿意把感受写下来。")

    suggestion_text = "；".join(str(s) for s in suggestions[:3]) if suggestions else "先做一件很小、能完成的事"
    return (
        f"{opening}\n\n"
        f"我初步识别到的主要情绪是“{emotion}”，强度约为“{intensity}”。"
        f"这不代表诊断，只是帮助你更清楚地看见当下状态。\n\n"
        f"现在可以先尝试：{suggestion_text}。\n\n"
        "如果这种状态持续影响睡眠、饮食、学习或安全感，建议联系学校心理中心、辅导员、朋友或家人。"
    )


def call_deepseek_reply(text: str, analysis: Dict[str, object], is_crisis: bool = False) -> Optional[str]:
    """可选的大模型接口。

    使用方法：
    1. 设置环境变量 DEEPSEEK_API_KEY；
    2. 可选设置 DEEPSEEK_BASE_URL，默认 https://api.deepseek.com/chat/completions。
    无 API key 时返回 None，由本地模板接管。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/chat/completions")
    emotion = analysis.get("emotion", "未知")
    intensity = analysis.get("intensity", "未知")

    user_prompt = f"""
用户输入：
{text}

系统识别：
- 情绪：{emotion}
- 强度：{intensity}
- 是否危机：{is_crisis}

请生成 120-180 字中文回应。要求：
1. 共情但不夸张；
2. 不做医学诊断；
3. 给 2-3 个可执行自我照护建议；
4. 若 is_crisis 为 True，必须建议立即联系真人、拨打 120/110/12356，不提供任何伤害方法。
""".strip()

    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": SYSTEM_SAFETY_RULES},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 500,
    }

    try:
        response = requests.post(
            base_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def generate_reply(text: str, analysis: Dict[str, object], is_crisis: bool = False) -> str:
    """优先使用大模型，无 API 时自动退化为本地模板。"""
    llm_reply = call_deepseek_reply(text, analysis, is_crisis=is_crisis)
    if llm_reply:
        return llm_reply
    return fallback_supportive_reply(text, analysis, is_crisis=is_crisis)
