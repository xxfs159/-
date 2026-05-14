from __future__ import annotations

import difflib
import re

from .models import Finding, PatchFile, SourceFile
from .scanner import SECRET_RE


def build_patch(files: list[SourceFile], findings: list[Finding]) -> tuple[str, list[PatchFile]]:
    findings_by_path: dict[str, list[Finding]] = {}
    for finding in findings:
        if finding.fixable:
            findings_by_path.setdefault(finding.file_path, []).append(finding)

    changed_files: list[PatchFile] = []
    diff_chunks: list[str] = []
    files_by_path = {source_file.path: source_file for source_file in files}

    for path, file_findings in findings_by_path.items():
        source_file = files_by_path.get(path)
        if not source_file:
            continue
        patched = apply_safe_fixes(source_file, file_findings)
        if patched != source_file.content:
            changed = PatchFile(path=path, original=source_file.content, patched=patched)
            changed_files.append(changed)
            diff_chunks.extend(
                difflib.unified_diff(
                    source_file.content.splitlines(keepends=True),
                    patched.splitlines(keepends=True),
                    fromfile=f"a/{path}",
                    tofile=f"b/{path}",
                )
            )

    return "".join(diff_chunks), changed_files


def apply_safe_fixes(source_file: SourceFile, findings: list[Finding]) -> str:
    line_findings: dict[int, list[Finding]] = {}
    for finding in findings:
        line_findings.setdefault(finding.line, []).append(finding)

    lines = source_file.content.splitlines()
    needs_os_import = False

    for line_number, related_findings in line_findings.items():
        if line_number < 1 or line_number > len(lines):
            continue
        line = lines[line_number - 1]
        for finding in related_findings:
            if finding.fix_kind == "hardcoded_secret":
                line, used_os = _fix_hardcoded_secret(line, source_file.language)
                needs_os_import = needs_os_import or used_os
            elif finding.fix_kind == "debug_true":
                line = re.sub(r"\bdebug\s*=\s*True\b", "debug=False", line)
                line = re.sub(r"\bDEBUG\s*=\s*True\b", "DEBUG = False", line)
            elif finding.fix_kind == "yaml_safe_load":
                line = re.sub(r"\byaml\.load\s*\(", "yaml.safe_load(", line)
            elif finding.fix_kind == "weak_hash":
                line = _fix_weak_hash(line)
        lines[line_number - 1] = line

    patched = "\n".join(lines)
    if source_file.content.endswith("\n"):
        patched += "\n"

    if needs_os_import:
        patched = _ensure_python_import_os(patched)

    return patched


def _fix_hardcoded_secret(line: str, language: str) -> tuple[str, bool]:
    match = SECRET_RE.search(line)
    if not match:
        return line, False

    name = _env_name(match.group("name"))
    prefix = match.group("prefix")

    if language == "python":
        replacement = f'{prefix}os.getenv("{name}", "")'
        return line[: match.start()] + replacement + line[match.end() :], True

    if language in {"javascript", "typescript"}:
        replacement = f'{prefix}process.env.{name} || ""'
        return line[: match.start()] + replacement + line[match.end() :], False

    replacement = f'{prefix}"${{{name}}}"'
    return line[: match.start()] + replacement + line[match.end() :], False


def _fix_weak_hash(line: str) -> str:
    line = re.sub(r"hashlib\.md5\s*\(", "hashlib.sha256(", line)
    line = re.sub(r"hashlib\.sha1\s*\(", "hashlib.sha256(", line)
    line = re.sub(r"""createHash\(\s*["']md5["']\s*\)""", 'createHash("sha256")', line, flags=re.IGNORECASE)
    line = re.sub(r"""createHash\(\s*["']sha1["']\s*\)""", 'createHash("sha256")', line, flags=re.IGNORECASE)
    line = re.sub(r"""getInstance\(\s*["']MD5["']\s*\)""", 'getInstance("SHA-256")', line, flags=re.IGNORECASE)
    line = re.sub(r"""getInstance\(\s*["']SHA-1["']\s*\)""", 'getInstance("SHA-256")', line, flags=re.IGNORECASE)
    return line


def _ensure_python_import_os(content: str) -> str:
    if re.search(r"(^|\n)\s*import\s+os(\s|$|,)", content) or re.search(r"(^|\n)\s*from\s+os\s+import\s+", content):
        return content

    lines = content.splitlines()
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if len(lines) > insert_at and "coding" in lines[insert_at]:
        insert_at += 1
    lines.insert(insert_at, "import os")
    patched = "\n".join(lines)
    if content.endswith("\n"):
        patched += "\n"
    return patched


def _env_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_") or "SECRET_VALUE"
