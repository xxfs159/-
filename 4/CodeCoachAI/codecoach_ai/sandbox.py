"""Tiny local sandbox runner for CodeCoach-AI.

This is a teaching-project sandbox, not a production-grade security sandbox.
Run only trusted code locally or isolate it with Docker/WSL when demonstrating.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class TestCase:
    name: str
    stdin: str
    expected: str


@dataclass
class TestResult:
    name: str
    passed: bool
    stdin: str
    expected: str
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False


@dataclass
class RunSummary:
    language: str
    compile_ok: bool
    compile_log: str
    results: List[TestResult]

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def total_count(self) -> int:
        return len(self.results)


def normalize_output(text: str) -> str:
    """Compare outputs in an OJ-like, whitespace-tolerant way."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()


def run_solution(language: str, code: str, test_cases: Iterable[TestCase], timeout_sec: int = 3) -> RunSummary:
    language = language.lower().strip()
    cases = list(test_cases)
    with tempfile.TemporaryDirectory(prefix="codecoach_") as td:
        workdir = Path(td)
        if language in {"python", "py", "python3"}:
            src = workdir / "main.py"
            src.write_text(code, encoding="utf-8")
            cmd = [os.environ.get("PYTHON", "python"), str(src)]
            return _run_cases(language="Python", cmd=cmd, cases=cases, timeout_sec=timeout_sec, compile_ok=True, compile_log="")

        if language in {"c++", "cpp", "cxx"}:
            src = workdir / "main.cpp"
            exe = workdir / "main"
            src.write_text(code, encoding="utf-8")
            compile_cmd = ["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", str(src), "-o", str(exe)]
            try:
                cp = subprocess.run(compile_cmd, cwd=workdir, capture_output=True, text=True, timeout=10)
            except FileNotFoundError:
                return RunSummary("C++17", False, "未找到 g++。请先安装 GCC / MinGW / WSL g++。", [])
            except subprocess.TimeoutExpired:
                return RunSummary("C++17", False, "编译超时。", [])
            if cp.returncode != 0:
                return RunSummary("C++17", False, cp.stderr or cp.stdout, [])
            return _run_cases(language="C++17", cmd=[str(exe)], cases=cases, timeout_sec=timeout_sec, compile_ok=True, compile_log=cp.stderr)

        return RunSummary(language, False, f"暂不支持语言：{language}。当前支持 Python / C++。", [])


def _run_cases(language: str, cmd: List[str], cases: List[TestCase], timeout_sec: int, compile_ok: bool, compile_log: str) -> RunSummary:
    results: List[TestResult] = []
    for idx, case in enumerate(cases, start=1):
        try:
            cp = subprocess.run(
                cmd,
                input=case.stdin,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            stdout = cp.stdout
            stderr = cp.stderr
            passed = normalize_output(stdout) == normalize_output(case.expected)
            results.append(
                TestResult(
                    name=case.name or f"样例 {idx}",
                    passed=passed,
                    stdin=case.stdin,
                    expected=case.expected,
                    stdout=stdout,
                    stderr=stderr,
                    returncode=cp.returncode,
                    timed_out=False,
                )
            )
        except subprocess.TimeoutExpired as e:
            results.append(
                TestResult(
                    name=case.name or f"样例 {idx}",
                    passed=False,
                    stdin=case.stdin,
                    expected=case.expected,
                    stdout=e.stdout or "",
                    stderr=(e.stderr or "") + f"\n运行超时：>{timeout_sec}s",
                    returncode=-1,
                    timed_out=True,
                )
            )
    return RunSummary(language=language, compile_ok=compile_ok, compile_log=compile_log, results=results)
