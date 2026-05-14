from __future__ import annotations

import json

from .models import Finding, SourceFile


SYSTEM_PROMPT = """You are a senior application security code reviewer.
Return only valid JSON. Focus on exploitable logic bugs and security risks.
Use concise Chinese descriptions for user-facing fields.
Prefer fixes that are small enough for a pull request."""


FEW_SHOT_EXAMPLES = [
    {
        "input": "cursor.execute(f\"SELECT * FROM users WHERE id={user_id}\")",
        "output": {
            "findings": [
                {
                    "title": "SQL 注入风险",
                    "severity": "critical",
                    "reason": "用户输入被直接拼接进 SQL。",
                    "fix": "改为 cursor.execute(\"SELECT * FROM users WHERE id=%s\", (user_id,))。",
                }
            ]
        },
    },
    {
        "input": "subprocess.run(cmd, shell=True)",
        "output": {
            "findings": [
                {
                    "title": "命令注入风险",
                    "severity": "critical",
                    "reason": "shell=True 会让攻击者控制 shell 语义。",
                    "fix": "使用参数数组并对命令做白名单校验。",
                }
            ]
        },
    },
]


def build_audit_prompt(files: list[SourceFile], findings: list[Finding], max_chars: int = 24000) -> str:
    selected_files = []
    used = 0
    for source_file in files:
        snippet = source_file.content[:6000]
        if used + len(snippet) > max_chars:
            break
        used += len(snippet)
        selected_files.append({"path": source_file.path, "language": source_file.language, "content": snippet})

    rule_findings = [
        {
            "title": finding.title,
            "severity": finding.severity,
            "file": finding.file_path,
            "line": finding.line,
            "evidence": finding.evidence,
            "recommendation": finding.recommendation,
        }
        for finding in findings[:50]
    ]

    payload = {
        "task": "Audit the uploaded project for security vulnerabilities and produce PR-level repair suggestions.",
        "output_schema": {
            "executive_summary": "string",
            "confirmed_findings": [
                {
                    "title": "string",
                    "severity": "critical|high|medium|low",
                    "file": "string",
                    "line": "number",
                    "why_exploitable": "string",
                    "patch_strategy": "string",
                }
            ],
            "pull_request_plan": ["string"],
        },
        "few_shot_examples": FEW_SHOT_EXAMPLES,
        "rule_findings": rule_findings,
        "files": selected_files,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
