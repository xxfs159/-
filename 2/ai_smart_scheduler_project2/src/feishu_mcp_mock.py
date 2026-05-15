from __future__ import annotations

import json
import pandas as pd


def plan_to_feishu_events(plan_df: pd.DataFrame) -> str:
    """将学习计划转换为飞书日历/任务同步所需的模拟 JSON。

    说明：课程演示版本不直接调用真实飞书接口，避免泄露 token 或依赖外部账号。
    后续接入飞书 MCP 时，可把这里生成的 payload 交给 MCP 工具执行。
    """
    events = []
    for _, row in plan_df.iterrows():
        events.append(
            {
                "summary": f"{row['任务']}（{row['课程']}）",
                "start_time": f"{row['日期']} {row['开始']}",
                "end_time": f"{row['日期']} {row['结束']}",
                "description": f"类型：{row['类型']}；优先级：{row['优先级']}；备注：{row['备注']}",
                "reminder_minutes": 15,
                "source": "AI智能课表与学习计划生成系统",
            }
        )
    return json.dumps({"events": events}, ensure_ascii=False, indent=2)
