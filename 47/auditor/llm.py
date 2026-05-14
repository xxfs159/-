from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .models import Finding, SourceFile
from .prompts import SYSTEM_PROMPT, build_audit_prompt


@dataclass(slots=True)
class LlmConfig:
    api_key: str
    base_url: str
    model: str
    provider: str


def load_config_from_env() -> LlmConfig | None:
    if os.getenv("DEEPSEEK_API_KEY"):
        return LlmConfig(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/chat/completions"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-coder"),
            provider="deepseek",
        )

    qwen_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if qwen_key:
        return LlmConfig(
            api_key=qwen_key,
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"),
            model=os.getenv("QWEN_MODEL", "qwen-coder-plus"),
            provider="qwen",
        )

    if os.getenv("LLM_API_KEY"):
        return LlmConfig(
            api_key=os.environ["LLM_API_KEY"],
            base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/chat/completions"),
            model=os.getenv("LLM_MODEL", "deepseek-coder"),
            provider=os.getenv("LLM_PROVIDER", "openai-compatible"),
        )

    return None


def enrich_with_llm(files: list[SourceFile], findings: list[Finding]) -> dict[str, Any]:
    config = load_config_from_env()
    prompt = build_audit_prompt(files, findings)
    if not config:
        return {
            "enabled": False,
            "message": "No LLM API key found. Set DEEPSEEK_API_KEY, QWEN_API_KEY, DASHSCOPE_API_KEY, or LLM_API_KEY.",
            "prompt_preview": prompt[:4000],
        }

    payload = {
        "model": config.model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        config.base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"enabled": True, "provider": config.provider, "error": f"HTTP {exc.code}: {body[:1000]}"}
    except Exception as exc:  # pragma: no cover - network dependent
        return {"enabled": True, "provider": config.provider, "error": str(exc)}

    content = _extract_message(data)
    return {
        "enabled": True,
        "provider": config.provider,
        "model": config.model,
        "content": content,
        "raw": data,
    }


def _extract_message(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return json.dumps(data, ensure_ascii=False)
    message = choices[0].get("message") or {}
    return message.get("content") or json.dumps(choices[0], ensure_ascii=False)
