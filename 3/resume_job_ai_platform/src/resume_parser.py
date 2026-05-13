from __future__ import annotations

import re
from pathlib import Path
from typing import BinaryIO

from .utils import normalize_text, unique_keep_order


SKILL_LIBRARY = [
    "Python", "Java", "C++", "SQL", "JavaScript", "HTML", "CSS", "Vue", "React",
    "Spring Boot", "MySQL", "Redis", "Git", "Flask", "FastAPI", "Streamlit",
    "Pandas", "NumPy", "Matplotlib", "Scikit-learn", "PyTorch", "TensorFlow",
    "机器学习", "深度学习", "NLP", "自然语言处理", "Transformer", "Embedding",
    "BGE", "RAG", "LangChain", "向量数据库", "Prompt工程", "DeepSeek",
    "数据分析", "数据清洗", "数据可视化", "特征工程", "模型评估",
    "需求分析", "原型设计", "用户研究", "产品设计", "Axure", "Figma",
    "招聘", "简历优化", "内容运营", "用户运营"
]


def extract_text_from_upload(uploaded_file) -> str:
    """从 Streamlit 上传文件中提取文本，支持 txt/pdf/docx。"""
    if uploaded_file is None:
        return ""

    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith(".txt"):
        for enc in ("utf-8", "gbk", "gb18030"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(data))
            texts = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(texts)
        except Exception as exc:
            return f"PDF解析失败：{exc}"

    if name.endswith(".docx"):
        try:
            from docx import Document
            import io

            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as exc:
            return f"DOCX解析失败：{exc}"

    return "暂不支持该文件格式，请上传 txt、pdf 或 docx 文件。"


def extract_skills(text: str) -> list[str]:
    """基于课程项目可解释性要求，采用技能词典抽取简历技能。"""
    if not text:
        return []

    found = []
    lower_text = text.lower()
    for skill in SKILL_LIBRARY:
        if skill.lower() in lower_text:
            found.append(skill)
    return unique_keep_order(found)


def extract_basic_info(text: str) -> dict:
    """抽取姓名、邮箱、电话、学历关键词等基础信息。"""
    text = text or ""
    email = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text)
    phone = re.search(r"(?:\+?86[- ]?)?1[3-9]\d{9}", text)

    # 简化姓名抽取：取第一行较短文本，避免过度复杂。
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0][:20] if lines else "未识别"

    education_keywords = []
    for kw in ["本科", "硕士", "博士", "计算机", "软件工程", "人工智能", "数据科学"]:
        if kw in text:
            education_keywords.append(kw)

    years = re.findall(r"(20\d{2})\.?\d{0,2}\s*[-—至到]\s*(20\d{2}|至今|现在)", text)
    return {
        "name": name,
        "email": email.group(0) if email else "未识别",
        "phone": phone.group(0) if phone else "未识别",
        "education_keywords": education_keywords,
        "time_ranges": years,
    }


def parse_resume(text: str) -> dict:
    """输出结构化简历信息。"""
    cleaned = normalize_text(text)
    skills = extract_skills(cleaned)
    basic = extract_basic_info(text)

    project_count = len(re.findall(r"项目|系统|平台|Demo|demo", text))
    bullet_count = len(re.findall(r"[-•●]\s*", text))

    return {
        "raw_text": text,
        "cleaned_text": cleaned,
        "basic_info": basic,
        "skills": skills,
        "project_count": project_count,
        "bullet_count": bullet_count,
        "summary": {
            "skill_count": len(skills),
            "project_count": project_count,
            "bullet_count": bullet_count,
        },
    }
