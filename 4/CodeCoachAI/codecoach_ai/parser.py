from __future__ import annotations

import json
from typing import List

from .sandbox import TestCase


DEFAULT_CASES = [TestCase(name="样例 1", stdin="1 2\n", expected="3\n")]


def parse_test_cases(text: str) -> List[TestCase]:
    """Parse test cases from JSON or a simple split format.

    JSON example:
    [
      {"name": "样例1", "input": "1 2\\n", "expected": "3\\n"}
    ]

    Split format:
    1 2
    ---
    3
    ===
    2 3
    ---
    5
    """
    text = (text or "").strip()
    if not text:
        return DEFAULT_CASES

    # JSON mode
    if text.startswith("["):
        data = json.loads(text)
        cases = []
        for i, item in enumerate(data, start=1):
            cases.append(
                TestCase(
                    name=item.get("name", f"样例 {i}"),
                    stdin=item.get("input", item.get("stdin", "")),
                    expected=item.get("expected", item.get("output", "")),
                )
            )
        return cases

    # Split mode
    cases: List[TestCase] = []
    chunks = [c.strip("\n") for c in text.split("===") if c.strip()]
    for i, chunk in enumerate(chunks, start=1):
        if "---" not in chunk:
            raise ValueError("测试用例格式错误：每个样例需要用 --- 分隔输入和期望输出。")
        stdin, expected = chunk.split("---", 1)
        cases.append(TestCase(name=f"样例 {i}", stdin=stdin.strip("\n") + "\n", expected=expected.strip("\n") + "\n"))
    return cases or DEFAULT_CASES
