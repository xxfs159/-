from __future__ import annotations

import json
import os
import urllib.request


def generate_ai_summary(plan_markdown: str) -> str:
    """可选的大模型总结模块。

    使用方法：
    1. 设置环境变量 DEEPSEEK_API_KEY。
    2. 如接口地址变化，可设置 DEEPSEEK_BASE_URL。
    3. 如果不设置 API Key，系统会自动返回本地模板总结，不影响演示。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/chat/completions").strip()

    if not api_key:
        return local_summary(plan_markdown)

    prompt = f"""你是学习规划助手。请根据下面的一周学习计划，生成：
1. 本周学习重点
2. 每天执行建议
3. 风险提醒
4. 鼓励语
要求简洁、具体、适合大学生执行。

计划：
{plan_markdown}
"""
    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": "你是严谨、温和、可执行的学习计划助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    req = urllib.request.Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as exc:
        return local_summary(plan_markdown) + f"\n\n> 说明：DeepSeek 调用失败，已回退到本地总结。错误：{exc}"


def local_summary(plan_markdown: str) -> str:
    return """### 本周学习建议

- 先完成高优先级、临近 DDL 的任务，避免最后一天集中赶工。
- 每个学习块控制在 30-120 分钟，学习后及时记录完成情况。
- 对项目类任务建议拆成“需求理解 → 原型开发 → 测试修复 → 报告整理 → 汇报演示”几个阶段。
- 每天晚上检查第二天计划，如果出现课程调整或临时任务，可以重新生成计划。

### 风险提醒

如果系统提示“可用时间不足”，说明当前空闲时间无法覆盖全部任务，需要增加空闲时段、降低任务耗时估计，或优先保障最重要任务。
"""
