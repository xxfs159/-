from __future__ import annotations

import os
from typing import Optional


def call_deepseek(prompt: str, temperature: float = 0.4) -> Optional[str]:
    """
    可选 DeepSeek 调用。

    没有配置 DEEPSEEK_API_KEY 时返回 None，系统自动使用本地模板。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一名专业的中文简历优化与求职辅导助手，输出具体、可执行、不过度夸大的建议。"},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"DeepSeek 调用失败，已切换到本地模板。错误信息：{exc}"


def generate_gap_analysis(resume_skills: list[str], job_row: dict) -> str:
    matched = job_row.get("matched_skills", "暂无")
    missing = job_row.get("missing_skills", "暂无")
    return f"""### 匹配差距分析

**目标岗位：{job_row.get('title')}｜{job_row.get('company')}**

- 已匹配能力：{matched}
- 主要缺口：{missing}
- 推荐结论：该岗位与当前简历的综合匹配度为 **{job_row.get('match_score')}%**。如果想提升竞争力，应优先补充岗位 JD 中反复出现的技能，并在项目经历中加入量化结果。
"""


def generate_resume_summary(resume_parse: dict, job_row: dict) -> str:
    prompt = f"""
请根据以下信息生成一段中文简历个人优势摘要，要求80-120字，突出与目标岗位的匹配点，不要编造不存在的经历。

目标岗位：{job_row.get('title')}
岗位要求：{job_row.get('requirements')}
简历技能：{resume_parse.get('skills')}
简历概况：{resume_parse.get('summary')}
"""
    ai_text = call_deepseek(prompt)
    if ai_text and not ai_text.startswith("DeepSeek 调用失败"):
        return ai_text

    skills = "、".join(resume_parse.get("skills", [])[:6]) or "数据分析、AI应用开发"
    return (
        f"具备{skills}等相关基础，能够完成文本处理、数据分析与小型Web应用开发。"
        f"曾参与课程项目和系统 Demo 建设，理解从需求分析、功能设计到结果展示的完整流程。"
        f"希望在{job_row.get('title')}方向继续提升大模型应用落地、岗位需求理解和产品化实现能力。"
    )


def generate_project_bullets(resume_parse: dict, job_row: dict) -> list[str]:
    missing = [s for s in str(job_row.get("missing_skills", "")).replace("无明显缺口", "").split("、") if s]
    add_skills = "、".join(missing[:3]) if missing else "岗位核心技能"

    return [
        f"围绕“{job_row.get('title')}”岗位要求，建议在项目经历中明确写出技术链路，例如数据采集、文本清洗、向量检索、结果生成与前端展示。",
        f"将项目成果量化表达，例如“构建包含 8 类岗位 JD 的知识库，实现 Top-K 岗位推荐与匹配度解释”。",
        f"如果具备相关基础，可补充 {add_skills} 的学习或实践记录，并说明自己完成了哪些模块。",
        "把“负责/参与”改为“使用什么方法解决什么问题并取得什么结果”，提升简历说服力。",
    ]


def generate_cover_letter(resume_parse: dict, job_row: dict) -> str:
    prompt = f"""
请为学生生成一封中文求职信，目标岗位如下：
岗位：{job_row.get('title')}
公司：{job_row.get('company')}
岗位要求：{job_row.get('requirements')}
简历技能：{resume_parse.get('skills')}
要求：300字以内，真诚、具体、不夸大。
"""
    ai_text = call_deepseek(prompt)
    if ai_text and not ai_text.startswith("DeepSeek 调用失败"):
        return ai_text

    skills = "、".join(resume_parse.get("skills", [])[:5]) or "Python、数据分析和AI应用开发"
    return f"""尊敬的招聘负责人：

您好！我正在申请贵公司的“{job_row.get('title')}”岗位。通过学习和项目实践，我掌握了{skills}等相关能力，并对岗位中提到的“{job_row.get('direction')}”方向有较强兴趣。

在课程项目中，我曾完成数据整理、功能设计、系统展示和报告撰写等工作，理解从需求分析到成果展示的基本流程。虽然我仍处于持续学习阶段，但我具备较强的自学能力和项目执行意识，愿意在实际任务中进一步提升专业能力。

期待有机会参与贵公司的相关工作，并在团队中持续学习、创造价值。谢谢您的阅读！
"""


def generate_interview_points(job_row: dict) -> list[str]:
    return [
        f"请准备解释：为什么你适合“{job_row.get('title')}”岗位？可以从技能、项目经历、学习意愿三方面回答。",
        "请准备讲清楚一个项目：背景是什么、你负责什么、用了什么技术、遇到什么问题、结果如何。",
        f"请复习岗位相关技能：{job_row.get('skills')}。",
        "请准备回答简历真实性问题，尤其是项目中哪些模块是自己独立完成的。",
        "请准备一个反问问题，例如：该岗位入职后主要参与哪些项目？团队如何评价实习生的产出？",
    ]


def build_markdown_report(resume_parse: dict, top_jobs, selected_job: dict) -> str:
    lines = [
        "# 智能简历优化与岗位推荐报告",
        "",
        "## 一、简历基础信息",
        f"- 姓名：{resume_parse.get('basic_info', {}).get('name')}",
        f"- 邮箱：{resume_parse.get('basic_info', {}).get('email')}",
        f"- 电话：{resume_parse.get('basic_info', {}).get('phone')}",
        f"- 识别技能：{'、'.join(resume_parse.get('skills', [])) or '未识别'}",
        "",
        "## 二、岗位推荐结果",
    ]

    for idx, row in top_jobs.iterrows():
        lines.append(f"{idx+1}. {row['title']}｜{row['company']}｜匹配度：{row['match_score']}%｜匹配技能：{row['matched_skills']}")

    lines.extend([
        "",
        "## 三、目标岗位分析",
        generate_gap_analysis(resume_parse.get("skills", []), selected_job),
        "",
        "## 四、简历摘要优化",
        generate_resume_summary(resume_parse, selected_job),
        "",
        "## 五、项目经历优化建议",
    ])

    for item in generate_project_bullets(resume_parse, selected_job):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 六、求职信草稿",
        generate_cover_letter(resume_parse, selected_job),
        "",
        "## 七、面试准备要点",
    ])

    for item in generate_interview_points(selected_job):
        lines.append(f"- {item}")

    return "\n".join(lines)
