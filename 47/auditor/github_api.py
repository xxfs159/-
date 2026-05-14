from __future__ import annotations

import base64
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Any

from .models import SUPPORTED_EXTENSIONS, SourceFile, normalize_path


API_ROOT = "https://api.github.com"
MAX_FILE_BYTES = 350_000
MAX_FILES = 350


class GitHubError(RuntimeError):
    pass


@dataclass(slots=True)
class GitHubRepo:
    owner: str
    repo: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass(slots=True)
class DownloadedRepository:
    repo: GitHubRepo
    default_branch: str
    files: list[SourceFile]


def parse_github_url(url: str) -> GitHubRepo:
    clean = url.strip()
    match = re.search(r"github\.com[:/](?P<owner>[^/\s]+)/(?P<repo>[^/\s#?]+)", clean)
    if not match:
        raise GitHubError("Invalid GitHub repository URL.")
    repo = match.group("repo")
    if repo.endswith(".git"):
        repo = repo[:-4]
    return GitHubRepo(owner=match.group("owner"), repo=repo)


def download_repository(url: str, token: str | None = None) -> DownloadedRepository:
    repo = parse_github_url(url)
    token = token or os.getenv("GITHUB_TOKEN")
    repo_meta = github_json("GET", f"/repos/{repo.full_name}", token=token)
    default_branch = repo_meta.get("default_branch") or "main"
    archive_url = f"{API_ROOT}/repos/{repo.full_name}/zipball/{urllib.parse.quote(default_branch)}"
    request = _request(archive_url, token=token)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            archive = response.read()
    except urllib.error.HTTPError as exc:
        raise GitHubError(_http_error_message(exc)) from exc

    files: list[SourceFile] = []
    with zipfile.ZipFile(io.BytesIO(archive)) as zip_file:
        for member in zip_file.infolist():
            if member.is_dir() or len(files) >= MAX_FILES:
                continue
            relative = _strip_archive_root(member.filename)
            if not _is_supported_code_file(relative) or member.file_size > MAX_FILE_BYTES:
                continue
            with zip_file.open(member) as handle:
                content = handle.read().decode("utf-8", errors="replace")
            files.append(SourceFile(path=relative, content=content))

    return DownloadedRepository(repo=repo, default_branch=default_branch, files=files)


def create_issue(url: str, title: str, body: str, token: str | None = None) -> dict[str, Any]:
    repo = parse_github_url(url)
    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubError("GITHUB_TOKEN is required to create an issue.")
    return github_json("POST", f"/repos/{repo.full_name}/issues", token=token, payload={"title": title, "body": body})


def create_pull_request(
    url: str,
    changed_files: list[dict[str, str]],
    title: str,
    body: str,
    token: str | None = None,
) -> dict[str, Any]:
    repo = parse_github_url(url)
    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubError("GITHUB_TOKEN is required to create a pull request.")
    if not changed_files:
        raise GitHubError("There are no changed files to commit.")

    repo_meta = github_json("GET", f"/repos/{repo.full_name}", token=token)
    base_branch = repo_meta.get("default_branch") or "main"
    base_ref = github_json("GET", f"/repos/{repo.full_name}/git/ref/heads/{base_branch}", token=token)
    base_sha = base_ref["object"]["sha"]
    branch = f"ai-audit-fix-{int(time.time())}"

    github_json(
        "POST",
        f"/repos/{repo.full_name}/git/refs",
        token=token,
        payload={"ref": f"refs/heads/{branch}", "sha": base_sha},
    )

    for item in changed_files:
        path = normalize_path(item["path"])
        content = item["patched"]
        sha = _content_sha(repo, path, base_branch, token)
        payload = {
            "message": f"fix: apply AI audit repair for {path}",
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        github_json(
            "PUT",
            f"/repos/{repo.full_name}/contents/{urllib.parse.quote(path, safe='/')}",
            token=token,
            payload=payload,
        )

    return github_json(
        "POST",
        f"/repos/{repo.full_name}/pulls",
        token=token,
        payload={"title": title, "body": body, "head": branch, "base": base_branch},
    )


def github_json(method: str, path: str, *, token: str | None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = path if path.startswith("http") else f"{API_ROOT}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = _request(url, token=token, data=data, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raise GitHubError(_http_error_message(exc)) from exc


def _content_sha(repo: GitHubRepo, path: str, branch: str, token: str) -> str | None:
    try:
        item = github_json(
            "GET",
            f"/repos/{repo.full_name}/contents/{urllib.parse.quote(path, safe='/')}?ref={urllib.parse.quote(branch)}",
            token=token,
        )
    except GitHubError as exc:
        if "404" in str(exc):
            return None
        raise
    return item.get("sha")


def _request(
    url: str,
    *,
    token: str | None,
    data: bytes | None = None,
    method: str = "GET",
) -> urllib.request.Request:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-vuln-audit-assistant",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"
    return urllib.request.Request(url, data=data, headers=headers, method=method)


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    return f"GitHub API error {exc.code}: {body[:1000]}"


def _strip_archive_root(path: str) -> str:
    parts = path.split("/", 1)
    return normalize_path(parts[1] if len(parts) == 2 else path)


def _is_supported_code_file(path: str) -> bool:
    suffix = os.path.splitext(path)[1].lower()
    blocked = ("/node_modules/", "/.git/", "/dist/", "/build/", "/vendor/", "/__pycache__/")
    return suffix in SUPPORTED_EXTENSIONS and not any(token in f"/{path}" for token in blocked)
