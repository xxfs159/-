from src.resume_parser import parse_resume
from src.rag_matcher import load_jobs, match_jobs


def test_parse_resume_skills():
    text = "我熟悉 Python、SQL、RAG、Streamlit 和 Prompt工程。"
    result = parse_resume(text)
    assert "Python" in result["skills"]
    assert "RAG" in result["skills"]


def test_match_jobs():
    text = "我会 Python、Streamlit、RAG、Prompt工程，希望做大模型应用。"
    resume = parse_resume(text)
    jobs = load_jobs("data/jobs.csv")
    result = match_jobs(text, resume["skills"], jobs, direction="大模型应用", top_k=3)
    assert len(result) == 3
    assert "match_score" in result.columns
