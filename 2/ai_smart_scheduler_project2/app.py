from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.deepseek_client import generate_ai_summary
from src.feishu_mcp_mock import plan_to_feishu_events
from src.nlp_parser import parse_tasks_from_text
from src.planner import daily_summary, generate_plan, plan_to_dataframe, rows_to_tasks
from src.utils import week_start

st.set_page_config(page_title="AI智能课表与学习计划生成系统", page_icon="📚", layout="wide")

st.title("📚 AI 智能课表与学习计划生成系统")
st.caption("项目2演示版：课程表导入 + 自然语言任务解析 + 规划型 Agent + 一周学习计划生成")

with st.sidebar:
    st.header("1. 数据导入")
    course_file = st.file_uploader("上传课程表 CSV", type=["csv"], key="course")
    task_file = st.file_uploader("上传任务/DDL CSV", type=["csv"], key="task")
    free_file = st.file_uploader("上传空闲时间 CSV", type=["csv"], key="free")

    st.header("2. 计划参数")
    start_day = st.date_input("计划开始日期（建议选择周一）", value=week_start(date.today()))
    days = st.slider("生成天数", 3, 14, 7)

    st.header("3. 示例格式")
    st.code("人工智能：下周三 23:59 AI大项目报告 截止，预计6小时，很重要\n高数：5月20日 20:00 章节复习 需要3小时")

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def read_uploaded_or_sample(uploaded, sample_path: str) -> pd.DataFrame:
    if uploaded is not None:
        return pd.read_csv(uploaded)
    return load_csv(sample_path)

course_df = read_uploaded_or_sample(course_file, "data/sample_courses.csv")
task_df = read_uploaded_or_sample(task_file, "data/sample_tasks.csv")
free_df = read_uploaded_or_sample(free_file, "data/sample_free_slots.csv")

tab1, tab2, tab3, tab4 = st.tabs(["🗓️ 数据预览", "✍️ 自然语言输入", "🤖 智能计划", "📤 导出与总结"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("课程表")
        st.dataframe(course_df, use_container_width=True)
    with c2:
        st.subheader("空闲时间")
        st.dataframe(free_df, use_container_width=True)
    st.subheader("已有任务")
    st.dataframe(task_df, use_container_width=True)

with tab2:
    st.subheader("自然语言添加任务")
    text = st.text_area(
        "每行输入一个任务，系统会自动识别 DDL、耗时、优先级和任务类型。",
        height=180,
        placeholder="例如：人工智能：下周三 23:59 AI大项目原型开发 截止，预计6小时，很重要",
    )
    parsed_df = pd.DataFrame()
    if text.strip():
        parsed_tasks = parse_tasks_from_text(text, base=start_day)
        parsed_df = pd.DataFrame([
            {
                "task_name": t.task_name,
                "course": t.course,
                "deadline": t.deadline.strftime("%Y-%m-%d %H:%M"),
                "estimated_hours": t.estimated_hours,
                "priority": t.priority,
                "task_type": t.task_type,
                "description": t.description,
            }
            for t in parsed_tasks
        ])
        st.success(f"已解析 {len(parsed_df)} 个任务")
        st.dataframe(parsed_df, use_container_width=True)
    else:
        st.info("可以先不输入，系统会使用 data/sample_tasks.csv 中的示例任务。")

with tab3:
    st.subheader("生成一周学习计划")
    if st.button("🚀 生成计划", type="primary"):
        all_tasks = rows_to_tasks(task_df)
        if not parsed_df.empty:
            parsed_df["deadline"] = pd.to_datetime(parsed_df["deadline"])
            all_tasks.extend(rows_to_tasks(parsed_df))

        plan, warnings = generate_plan(
            tasks=all_tasks,
            course_df=course_df,
            free_df=free_df,
            start_day=start_day,
            days=days,
        )
        plan_df = plan_to_dataframe(plan)
        st.session_state["plan_df"] = plan_df
        st.session_state["warnings"] = warnings

    plan_df = st.session_state.get("plan_df", pd.DataFrame())
    warnings = st.session_state.get("warnings", [])

    if plan_df.empty:
        st.warning("尚未生成计划。点击上方按钮开始规划。")
    else:
        st.dataframe(plan_df, use_container_width=True)
        st.subheader("每日学习时长统计")
        st.bar_chart(daily_summary(plan_df), x="日期", y="学习时长(小时)")

        if warnings:
            st.warning("部分任务未完全安排，请查看原因：")
            st.dataframe(pd.DataFrame(warnings), use_container_width=True)
        else:
            st.success("所有任务均已安排到可用时间段。")

with tab4:
    st.subheader("导出计划与 AI 总结")
    plan_df = st.session_state.get("plan_df", pd.DataFrame())
    if plan_df.empty:
        st.info("请先在“智能计划”页生成计划。")
    else:
        csv_data = plan_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("下载计划 CSV", data=csv_data, file_name="weekly_study_plan.csv", mime="text/csv")

        markdown = plan_df.to_markdown(index=False)
        st.download_button("下载计划 Markdown", data=markdown.encode("utf-8"), file_name="weekly_study_plan.md", mime="text/markdown")

        feishu_json = plan_to_feishu_events(plan_df)
        st.download_button(
            "下载飞书 MCP 同步模拟 JSON",
            data=feishu_json.encode("utf-8"),
            file_name="feishu_mcp_events.json",
            mime="application/json",
        )

        with st.expander("生成 AI 学习建议", expanded=True):
            summary = generate_ai_summary(markdown)
            st.markdown(summary)
