from ai_emotion_treehole.crisis import detect_crisis
from ai_emotion_treehole.emotion_core import analyze_emotion


def test_analyze_pressure():
    result = analyze_emotion("项目DDL太多了，我晚上睡不着，真的压力好大")
    assert result["emotion"] in {"压力", "焦虑"}


def test_analyze_positive():
    result = analyze_emotion("今天展示很顺利，老师表扬了我们，我很开心")
    assert result["emotion"] == "积极"


def test_crisis_detection():
    is_crisis, category, hits = detect_crisis("我不想活了，感觉撑不下去了")
    assert is_crisis is True
    assert category in {"self_harm", "extreme_hopeless"}
    assert hits
