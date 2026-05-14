# Project 47: AI Vulnerability Code Audit Assistant

This project implements the requested tool for project 47:

- Accept local source files from the browser or fetch a GitHub repository through the GitHub API.
- Detect common logic and security risks with a deterministic audit engine.
- Optionally call DeepSeek-Coder, Qwen-Coder, or any OpenAI-compatible code model with a few-shot security prompt.
- Generate a vulnerability report, safe automatic fixes, a unified diff, an issue body, and a PR body.
- Create GitHub issues and pull requests when `GITHUB_TOKEN` has repository permission.

## Quick Start

```powershell
cd C:\Users\12808\Documents\Codex\2026-05-14\files-mentioned-by-the-user-1\ai-vuln-audit-assistant
python server.py
```

Open `http://127.0.0.1:8765`.

## Optional API Keys

DeepSeek:

```powershell
$env:DEEPSEEK_API_KEY="sk-..."
$env:DEEPSEEK_MODEL="deepseek-coder"
```

Qwen / DashScope compatible mode:

```powershell
$env:DASHSCOPE_API_KEY="sk-..."
$env:QWEN_MODEL="qwen-coder-plus"
```

Generic OpenAI-compatible endpoint:

```powershell
$env:LLM_API_KEY="sk-..."
$env:LLM_BASE_URL="https://your-provider.example/v1/chat/completions"
$env:LLM_MODEL="your-code-model"
```

GitHub issue and PR creation:

```powershell
$env:GITHUB_TOKEN="github_pat_..."
```

The PR workflow creates a branch named `ai-audit-fix-<timestamp>`, commits the generated safe fixes, and opens a pull request against the default branch. The token must have write access to the target repository.

## Tests

```powershell
python -m unittest discover -s tests
```

## Implementation Notes

The built-in rules cover SQL injection, command injection, hardcoded credentials, unsafe deserialization, dynamic execution, weak hashes, Flask debug mode, broad CORS, path traversal, SSRF sinks, and DOM XSS sinks.

The automatic patcher only changes low-risk mechanical fixes, such as moving Python secrets to `os.getenv`, disabling Flask debug mode, replacing unsafe `yaml.load`, and upgrading weak hash calls to SHA-256. Higher-risk findings remain in the report for human review.
