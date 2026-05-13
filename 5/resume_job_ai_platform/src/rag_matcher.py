from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .utils import normalize_text, split_items


def load_jobs(path: str = "data/jobs.csv") -> pd.DataFrame:
    """读取岗位知识库。"""
    jobs = pd.read_csv(path)
    required = {"job_id", "title", "company", "city", "salary", "direction", "skills", "description", "requirements"}
    missing = required - set(jobs.columns)
    if missing:
        raise ValueError(f"岗位知识库缺少字段：{missing}")
    return jobs


def build_job_document(row: pd.Series) -> str:
    """将一条岗位记录拼接成可检索文档。"""
    return " ".join([
        str(row.get("title", "")),
        str(row.get("direction", "")),
        str(row.get("skills", "")),
        str(row.get("description", "")),
        str(row.get("requirements", "")),
    ])


def calculate_skill_overlap(resume_skills: list[str], job_skills: list[str]) -> tuple[float, list[str], list[str]]:
    """计算简历技能与岗位技能的重合程度。"""
    resume_lower = {s.lower(): s for s in resume_skills}
    matched = []
    missing = []

    for skill in job_skills:
        if skill.lower() in resume_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    score = len(matched) / max(len(job_skills), 1)
    return score, matched, missing


def match_jobs(resume_text: str, resume_skills: list[str], jobs: pd.DataFrame, direction: str = "", top_k: int = 5) -> pd.DataFrame:
    """
    RAG 检索与综合匹配。

    这里将岗位 JD 看作知识库，将简历文本看作查询 Query：
    1. 对岗位文档和简历做 TF-IDF 字符 n-gram 向量化；
    2. 计算余弦相似度作为语义相关性；
    3. 融合技能重合度和求职方向匹配，得到最终分数。
    """
    resume_text = normalize_text(resume_text)
    docs = [build_job_document(row) for _, row in jobs.iterrows()]
    corpus = [resume_text + " " + " ".join(resume_skills) + " " + direction] + docs

    # 字符 n-gram 对中文和英文混合文本都比较稳，不依赖分词器。
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
    matrix = vectorizer.fit_transform(corpus)
    resume_vec = matrix[0]
    job_vecs = matrix[1:]

    semantic_scores = cosine_similarity(resume_vec, job_vecs).flatten()

    rows = []
    for idx, (_, row) in enumerate(jobs.iterrows()):
        job_skills = split_items(row["skills"])
        skill_score, matched, missing = calculate_skill_overlap(resume_skills, job_skills)
        direction_score = 1.0 if direction and direction.lower() in str(row["direction"]).lower() else 0.0

        final_score = 0.55 * semantic_scores[idx] + 0.35 * skill_score + 0.10 * direction_score
        final_score = float(np.clip(final_score, 0, 1))

        rows.append({
            "job_id": row["job_id"],
            "title": row["title"],
            "company": row["company"],
            "city": row["city"],
            "salary": row["salary"],
            "direction": row["direction"],
            "semantic_score": round(float(semantic_scores[idx]), 4),
            "skill_score": round(float(skill_score), 4),
            "direction_score": direction_score,
            "match_score": round(final_score * 100, 2),
            "matched_skills": "、".join(matched) if matched else "暂无明显匹配",
            "missing_skills": "、".join(missing[:8]) if missing else "无明显缺口",
            "description": row["description"],
            "requirements": row["requirements"],
            "skills": row["skills"],
        })

    result = pd.DataFrame(rows).sort_values("match_score", ascending=False).head(top_k)
    return result.reset_index(drop=True)
