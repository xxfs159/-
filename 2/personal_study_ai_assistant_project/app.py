from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import course_summary, generate_next_week_plan, identify_weak_points, knowledge_summary, load_all_data, weekly_review
from src.chatbot import answer_question
from src.database import get_connection, init_db, insert_note, insert_problem, insert_study_session, save_report
from src.report_generator import DeepSeekReportGenerator
from src.seed_data import seed_sample_data

st.set_page_config(page_title="个人学习档案 AI 助理", page_icon="📚", layout="wide")


@st.cache_resource
def init_app():
    seed_sample_data(force=False)
    conn = get_connection()
    init_db(conn)
    return conn


def reload_data(conn):
    return load_all_data(conn)


conn = init_app()
data = reload_data(conn)

st.title("📚 个人学习档案 AI 助理")
st.caption("聚合课程成绩、刷题记录、笔记和学习时长，自动生成周度学习复盘、薄弱点诊断和下周计划。")

with st.sidebar:
    st.header("系统说明")
    st.write("本项目使用 Streamlit + SQLite + Pandas 实现。DeepSeek API 为可选项；未配置 API Key 时会使用本地规则生成报告。")
    if st.button("重置为演示数据"):
        seed_sample_data(force=True)
        st.cache_resource.clear()
        st.rerun()

tabs = st.tabs(["📊 学习画像看板", "📝 数据录入", "🤖 AI 周报", "💬 自然语言查询", "📌 项目说明"])

with tabs[0]:
    data = reload_data(conn)
    course_df = course_summary(data)
    weak_df = identify_weak_points(data, top_n=5)
    weekly = weekly_review(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("本周学习时长", f"{weekly['study_hours']} h")
    c2.metric("本周刷题数", f"{weekly['total_problems']} 道")
    c3.metric("本周正确率", f"{weekly['accuracy']:.0%}")
    c4.metric("平均专注度", f"{weekly['avg_focus']} / 5")

    st.subheader("课程综合画像")
    show_df = course_df.copy()
    if not show_df.empty:
        show_df["avg_score"] = (show_df["avg_score"] * 100).round(1)
        show_df["accuracy"] = (show_df["accuracy"] * 100).round(1)
        show_df["study_hours"] = show_df["study_hours"].round(1)
    st.dataframe(
        show_df[["course_name", "category", "avg_score", "practice_count", "accuracy", "study_hours", "avg_focus"]],
        use_container_width=True,
    )

    left, right = st.columns(2)
    with left:
        if not course_df.empty:
            fig = px.bar(course_df, x="course_name", y="accuracy", title="各课程刷题正确率", text_auto=".0%")
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)
    with right:
        if not data["sessions"].empty:
            sessions = data["sessions"].copy()
            sessions["date"] = pd.to_datetime(sessions["start_time"]).dt.date
            daily = sessions.groupby("date", as_index=False)["duration_minutes"].sum()
            fig = px.line(daily, x="date", y="duration_minutes", markers=True, title="每日学习时长趋势")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("薄弱知识点 Top 5")
    if weak_df.empty:
        st.info("暂无薄弱点数据，请先录入刷题记录。")
    else:
        display = weak_df[["course_name", "knowledge_point", "practice_count", "wrong_count", "accuracy", "main_wrong_reason", "weakness_score"]].copy()
        display["accuracy"] = (display["accuracy"] * 100).round(1)
        display["weakness_score"] = display["weakness_score"].round(3)
        st.dataframe(display, use_container_width=True)

with tabs[1]:
    st.subheader("录入刷题记录")
    with st.form("problem_form"):
        col1, col2 = st.columns(2)
        course_name = col1.text_input("课程名称", value="人工智能引论")
        knowledge_point = col2.text_input("知识点", value="搜索算法")
        question_title = st.text_input("题目名称", value="A* 搜索算法练习题")
        col3, col4, col5 = st.columns(3)
        is_correct = col3.selectbox("是否做对", ["做对", "做错"]) == "做对"
        difficulty = col4.selectbox("难度", ["易", "中", "难"], index=1)
        platform = col5.text_input("题目来源", value="课堂练习")
        col6, col7 = st.columns(2)
        practice_date = col6.date_input("练习日期", value=date.today())
        time_spent = col7.number_input("耗时（分钟）", min_value=1, max_value=180, value=15)
        wrong_reason = st.text_input("错因（做错时填写）", value="概念不熟")
        submitted = st.form_submit_button("保存刷题记录")
        if submitted:
            insert_problem(conn, course_name, knowledge_point, question_title, is_correct, difficulty, platform, practice_date.isoformat(), int(time_spent), wrong_reason)
            st.success("刷题记录已保存。")
            st.rerun()

    st.divider()
    st.subheader("录入学习时长")
    with st.form("session_form"):
        col1, col2 = st.columns(2)
        s_course = col1.text_input("学习课程", value="人工智能引论")
        duration = col2.number_input("学习时长（分钟）", min_value=5, max_value=300, value=45)
        col3, col4 = st.columns(2)
        activity_type = col3.selectbox("学习类型", ["预习", "复习", "刷题", "整理笔记", "项目实践"])
        focus_score = col4.slider("专注度 1-5", min_value=1, max_value=5, value=4)
        remark = st.text_input("备注", value="状态稳定")
        if st.form_submit_button("保存学习时长"):
            insert_study_session(conn, s_course, datetime.now().isoformat(timespec="minutes"), int(duration), activity_type, int(focus_score), remark)
            st.success("学习时长已保存。")
            st.rerun()

    st.divider()
    st.subheader("录入学习笔记")
    with st.form("note_form"):
        n_course = st.text_input("笔记课程", value="人工智能引论")
        n_kp = st.text_input("笔记知识点", value="机器学习基础")
        n_title = st.text_input("笔记标题", value="监督学习与无监督学习区别")
        n_content = st.text_area("笔记内容", value="监督学习有标签，无监督学习主要发现数据结构。")
        if st.form_submit_button("保存笔记"):
            insert_note(conn, n_course, n_kp, n_title, n_content, date.today().isoformat())
            st.success("笔记已保存。")
            st.rerun()

with tabs[2]:
    st.subheader("AI 周度学习复盘报告")
    st.write("点击按钮后，系统会根据 SQLite 中的成绩、刷题、笔记和学习时长生成 Markdown 周报。")
    if st.button("生成本周 AI 复盘报告"):
        generator = DeepSeekReportGenerator()
        report = generator.generate(reload_data(conn))
        save_report(conn, f"{weekly['week_start']}~{weekly['week_end']}", report, datetime.now().isoformat(timespec="seconds"))
        st.markdown(report)
        st.download_button("下载 Markdown 周报", data=report, file_name="weekly_study_report.md", mime="text/markdown")

with tabs[3]:
    st.subheader("自然语言查询个人学习情况")
    st.write("示例：我最薄弱的知识点是什么？我下周应该怎么安排？我的刷题正确率如何？")
    question = st.text_input("请输入你的问题")
    if question:
        st.markdown(answer_question(question, reload_data(conn)))

with tabs[4]:
    st.subheader("项目亮点")
    st.markdown(
        """
- **学习档案闭环**：课程成绩、刷题、笔记、学习时长统一存入 SQLite。
- **可解释诊断**：薄弱点不是黑盒判断，而由正确率、错题数、难度、笔记数量综合计算。
- **AI 复盘能力**：支持 DeepSeek 生成周报；未配置 API Key 时仍可本地演示。
- **自然语言查询**：用户可以直接问“我哪里最薄弱”“下周学什么”。
- **适合作业展示**：包含看板、数据录入、周报、聊天四个演示环节。
        """
    )
