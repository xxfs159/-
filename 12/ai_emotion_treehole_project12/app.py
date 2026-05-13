from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ai_emotion_treehole.crisis import build_crisis_message, detect_crisis
from ai_emotion_treehole.emotion_core import EMOTION_COLORS, analyze_emotion, summarize_trend
from ai_emotion_treehole.response_generator import generate_reply
from ai_emotion_treehole.storage import clear_records, list_records, save_record


ROOT = Path(__file__).resolve().parent
RESOURCES = json.loads((ROOT / "data" / "resources.json").read_text(encoding="utf-8"))


st.set_page_config(
    page_title="AI 陪聊情绪树洞",
    page_icon="🌳",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: .2rem;
    }
    .sub-title {
        color: #666;
        margin-bottom: 1.5rem;
    }
    .safe-box {
        padding: 1rem;
        border-radius: 12px;
        background: #fff7ed;
        border: 1px solid #fed7aa;
    }
    .danger-box {
        padding: 1rem;
        border-radius: 12px;
        background: #fef2f2;
        border: 1px solid #fecaca;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 12px;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🌳 AI 陪聊情绪树洞</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">匿名记录情绪 · 自动识别情绪类型 · 生成陪伴式回应 · 保存情绪趋势 · 高风险表达转介提醒</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("项目说明")
    st.info(RESOURCES["disclaimer"])
    st.markdown("**本地演示模式**：不填写 API Key 也能运行，系统使用可解释规则和模板回应。")
    st.markdown("**增强模式**：设置 `DEEPSEEK_API_KEY` 后，可由大模型生成更自然的陪伴式回应。")
    st.divider()
    st.markdown("### 心理支持资源")
    for item in RESOURCES["china_national"]:
        st.write(f"**{item['name']}**：{item['phone']}")
        st.caption(item["note"])
    st.divider()
    if st.button("清空本地历史记录"):
        clear_records()
        st.success("已清空。请刷新页面查看。")

tab_chat, tab_trend, tab_about = st.tabs(["💬 情绪树洞", "📈 情绪趋势", "🧪 项目设计"])

with tab_chat:
    col_input, col_result = st.columns([1.1, 1])

    with col_input:
        st.subheader("写下此刻的心情")
        nickname = st.text_input("昵称（可不填）", placeholder="匿名用户")
        user_text = st.text_area(
            "你可以写烦恼、压力、日常心情或想对树洞说的话",
            height=230,
            placeholder="例如：最近期末考试和项目DDL都挤在一起，我晚上总是睡不着，感觉自己来不及了……",
        )

        col_a, col_b = st.columns([1, 1])
        submit = col_a.button("分析并回应", type="primary", use_container_width=True)
        sample = col_b.button("填入示例", use_container_width=True)

        if sample:
            st.session_state["sample_text"] = "最近期末考试和项目DDL挤在一起，我总觉得来不及，晚上睡不着。"
            st.rerun()

        if "sample_text" in st.session_state and not user_text:
            user_text = st.session_state.pop("sample_text")

    with col_result:
        st.subheader("AI 回应")
        if submit:
            if not user_text.strip():
                st.warning("请先输入一段文字。")
            else:
                analysis = analyze_emotion(user_text)
                is_crisis, crisis_type, hits = detect_crisis(user_text)
                reply = generate_reply(user_text, analysis, is_crisis=is_crisis)
                save_record(
                    text=user_text,
                    analysis=analysis,
                    reply=reply,
                    nickname=nickname or "匿名用户",
                    is_crisis=is_crisis,
                )

                if is_crisis:
                    st.markdown('<div class="danger-box">⚠️ <b>检测到高风险表达</b></div>', unsafe_allow_html=True)
                    st.error(build_crisis_message())
                    st.caption(f"命中类别：{crisis_type}；关键词：{', '.join(hits)}")

                emotion = str(analysis["emotion"])
                st.metric("主要情绪", emotion, f"置信度 {analysis['confidence']}")
                st.write(f"**强度：** {analysis['intensity']}")
                st.caption(str(analysis["reason"]))
                st.markdown("#### 陪伴式回应")
                st.write(reply)

                st.markdown("#### 自我照护建议")
                for s in analysis["suggestions"]:
                    st.write(f"- {s}")

                if is_crisis:
                    st.markdown("#### 立即可联系的资源")
                    for item in RESOURCES["china_national"] + RESOURCES["campus"]:
                        st.write(f"- **{item['name']}**：{item['phone']}（{item['note']}）")
        else:
            st.markdown(
                '<div class="safe-box">输入心情后，系统会显示情绪识别结果、解释、陪伴回应和照护建议。</div>',
                unsafe_allow_html=True,
            )

with tab_trend:
    st.subheader("历史情绪记录与可视化")
    records = list_records(limit=200)
    if not records:
        st.info("暂无记录。先到“情绪树洞”输入一段心情。")
    else:
        df = pd.DataFrame(records)
        df["created_at"] = pd.to_datetime(df["created_at"])
        st.write(summarize_trend(records))

        col1, col2 = st.columns(2)
        with col1:
            count_df = df.groupby("emotion").size().reset_index(name="次数")
            fig_bar = px.bar(count_df, x="emotion", y="次数", title="情绪类型分布", color="emotion",
                             color_discrete_map=EMOTION_COLORS)
            st.plotly_chart(fig_bar, use_container_width=True)
        with col2:
            fig_line = px.line(df, x="created_at", y="confidence", color="emotion",
                               title="情绪识别置信度变化", markers=True,
                               color_discrete_map=EMOTION_COLORS)
            st.plotly_chart(fig_line, use_container_width=True)

        st.dataframe(
            df[["created_at", "nickname", "emotion", "confidence", "intensity", "is_crisis", "text", "reply"]],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "导出 CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="emotion_records.csv",
            mime="text/csv",
        )

with tab_about:
    st.subheader("项目设计摘要")
    st.markdown(
        """
        **问题定义**：大学生常因学业、人际、就业等压力产生情绪困扰，但不一定愿意立即向他人倾诉。
        本项目提供低门槛匿名树洞，帮助用户完成情绪表达、初步识别、支持性回应和资源转介。

        **核心流程**：
        1. 用户匿名输入心情文本；
        2. 系统通过情绪词典和规则识别焦虑、低落、愤怒、孤独、压力、平静、积极等情绪；
        3. 检测自伤、自杀、极端绝望等高风险表达；
        4. 普通场景生成陪伴式回应和自我照护建议；
        5. 高风险场景显示危机提醒和现实资源转介；
        6. SQLite 保存情绪记录，用图表展示趋势。

        **创新点**：
        - 将“匿名树洞 + 情绪识别 + 大模型陪伴 + 危机转介”整合为完整闭环；
        - 使用可解释词典规则，适合课程展示和答辩；
        - 支持本地模板和 DeepSeek API 双模式，兼顾可运行性与生成效果。
        """
    )
