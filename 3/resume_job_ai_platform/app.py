from __future__ import annotations

import pandas as pd
import streamlit as st

from src.resume_parser import extract_text_from_upload, parse_resume
from src.rag_matcher import load_jobs, match_jobs
from src.generator import (
    build_markdown_report,
    generate_gap_analysis,
    generate_resume_summary,
    generate_project_bullets,
    generate_cover_letter,
    generate_interview_points,
)


st.set_page_config(
    page_title="智能简历优化与岗位推荐平台",
    page_icon="🧭",
    layout="wide",
)


@st.cache_data
def cached_jobs():
    return load_jobs("data/jobs.csv")


def load_sample_resume() -> str:
    with open("samples/resume_example.txt", "r", encoding="utf-8") as f:
        return f.read()


st.title("🧭 智能简历优化与岗位推荐平台")
st.caption("RAG岗位知识库 + 简历解析 + 匹配度评估 + 简历优化生成")

with st.sidebar:
    st.header("输入信息")
    uploaded = st.file_uploader("上传简历文件（txt/pdf/docx）", type=["txt", "pdf", "docx"])
    use_sample = st.checkbox("使用示例简历", value=True if uploaded is None else False)

    direction_options = [
        "大模型应用", "AI产品", "算法/NLP", "数据分析", "后端开发", "前端开发", "机器学习", "产品运营"
    ]
    direction = st.selectbox("求职方向", direction_options)
    top_k = st.slider("推荐岗位数量", 3, 8, 5)
    run = st.button("开始智能匹配", type="primary")

jobs = cached_jobs()

if uploaded is not None:
    resume_text = extract_text_from_upload(uploaded)
elif use_sample:
    resume_text = load_sample_resume()
else:
    resume_text = st.text_area("请粘贴简历文本", height=260)

if not resume_text:
    st.info("请上传简历、使用示例简历，或手动粘贴简历文本。")
    st.stop()

resume_parse = parse_resume(resume_text)

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("识别技能数", resume_parse["summary"]["skill_count"])
with col_b:
    st.metric("项目关键词数", resume_parse["summary"]["project_count"])
with col_c:
    st.metric("简历条目数", resume_parse["summary"]["bullet_count"])

with st.expander("查看简历解析结果", expanded=False):
    st.write("基础信息：", resume_parse["basic_info"])
    st.write("技能关键词：", "、".join(resume_parse["skills"]) or "未识别")
    st.text_area("简历原文", resume_text, height=220)

if run or use_sample:
    result = match_jobs(resume_text, resume_parse["skills"], jobs, direction=direction, top_k=top_k)

    st.subheader("岗位推荐 Top-K")
    display_cols = ["title", "company", "city", "salary", "direction", "match_score", "matched_skills", "missing_skills"]
    st.dataframe(result[display_cols], use_container_width=True, hide_index=True)

    chart_data = result[["title", "match_score"]].set_index("title")
    st.bar_chart(chart_data)

    selected_title = st.selectbox("选择一个目标岗位生成优化内容", result["title"].tolist())
    selected = result[result["title"] == selected_title].iloc[0].to_dict()

    left, right = st.columns([1, 1])
    with left:
        st.subheader("匹配解释")
        st.markdown(generate_gap_analysis(resume_parse["skills"], selected))
        st.markdown("### 岗位 JD")
        st.write(selected["description"])
        st.write(selected["requirements"])

    with right:
        st.subheader("简历摘要优化")
        st.info(generate_resume_summary(resume_parse, selected))

        st.markdown("### 项目经历优化建议")
        for item in generate_project_bullets(resume_parse, selected):
            st.write("- " + item)

    st.subheader("定制化求职信")
    st.markdown(generate_cover_letter(resume_parse, selected))

    st.subheader("面试准备要点")
    for item in generate_interview_points(selected):
        st.write("- " + item)

    report = build_markdown_report(resume_parse, result, selected)
    st.download_button(
        "下载 Markdown 求职优化报告",
        data=report.encode("utf-8"),
        file_name="resume_job_match_report.md",
        mime="text/markdown",
    )

else:
    st.info("点击左侧按钮开始匹配。")
