from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from auditor.github_api import GitHubError, create_issue, create_pull_request, download_repository
from auditor.llm import enrich_with_llm
from auditor.models import AuditResult, SourceFile, normalize_path
from auditor.patcher import build_patch
from auditor.report import issue_body, pull_request_body, summarize
from auditor.scanner import scan_files


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
MAX_BODY_BYTES = 15 * 1024 * 1024


class AuditHandler(BaseHTTPRequestHandler):
    server_version = "AIVulnAudit/1.0"

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if self.path.startswith("/static/"):
            relative = normalize_path(self.path.removeprefix("/static/"))
            target = (STATIC_DIR / relative).resolve()
            if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR.resolve():
                self._json({"error": "Invalid static path"}, status=400)
                return
            self._send_file(target)
            return
        self._json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/audit":
                self._handle_audit()
            elif self.path == "/api/github/issue":
                self._handle_issue()
            elif self.path == "/api/github/pr":
                self._handle_pr()
            else:
                self._json({"error": "Not found"}, status=404)
        except GitHubError as exc:
            self._json({"error": str(exc)}, status=502)
        except ValueError as exc:
            self._json({"error": str(exc)}, status=400)
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            self._json({"error": f"Unexpected server error: {exc}"}, status=500)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[server] {self.address_string()} - {fmt % args}")

    def _handle_audit(self) -> None:
        payload = self._read_json()
        github_url = (payload.get("github_url") or "").strip()
        use_llm = bool(payload.get("use_llm"))
        source_files: list[SourceFile]
        github_meta: dict[str, Any] | None = None

        if github_url:
            downloaded = download_repository(github_url)
            source_files = downloaded.files
            github_meta = {
                "repo": downloaded.repo.full_name,
                "default_branch": downloaded.default_branch,
                "files_loaded": len(downloaded.files),
            }
        else:
            source_files = _files_from_payload(payload)

        if not source_files:
            raise ValueError("No supported source files were provided.")

        findings = scan_files(source_files)
        patch, changed_files = build_patch(source_files, findings)
        llm = enrich_with_llm(source_files, findings) if use_llm else {"enabled": False}
        result = AuditResult(
            summary=summarize(findings, len(source_files)),
            findings=findings,
            patch=patch,
            changed_files=changed_files,
            llm=llm,
        ).to_dict()
        result["github"] = github_meta
        result["issue_body"] = issue_body(findings, patch)
        result["pull_request_body"] = pull_request_body(findings, patch)
        self._json(result)

    def _handle_issue(self) -> None:
        payload = self._read_json()
        github_url = (payload.get("github_url") or "").strip()
        title = payload.get("title") or "AI vulnerability audit report"
        body = payload.get("body") or ""
        if not github_url or not body:
            raise ValueError("github_url and body are required.")
        issue = create_issue(github_url, title, body)
        self._json({"issue": issue})

    def _handle_pr(self) -> None:
        payload = self._read_json()
        github_url = (payload.get("github_url") or "").strip()
        changed_files = payload.get("changed_files") or []
        title = payload.get("title") or "fix: apply AI vulnerability audit repairs"
        body = payload.get("body") or ""
        if not github_url or not changed_files:
            raise ValueError("github_url and changed_files are required.")
        pull = create_pull_request(github_url, changed_files, title, body)
        self._json({"pull_request": pull})

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body is too large.")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _json(self, data: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            self._json({"error": "File not found"}, status=404)
            return
        data = path.read_bytes()
        mime = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if mime.startswith("text/") and "charset" not in mime:
            mime += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _files_from_payload(payload: dict[str, Any]) -> list[SourceFile]:
    files = []
    for item in payload.get("files") or []:
        path = item.get("path") or "untitled.txt"
        content = item.get("content")
        if not isinstance(content, str):
            continue
        if len(content.encode("utf-8")) > 350_000:
            continue
        files.append(SourceFile(path=path, content=content))
    return files[:350]


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8765"))
    server = ThreadingHTTPServer((host, port), AuditHandler)
    print(f"AI vulnerability audit assistant is running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
