from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import PurePosixPath
from typing import Any


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".php": "php",
    ".rb": "ruby",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
}


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


@dataclass(slots=True)
class SourceFile:
    path: str
    content: str
    language: str = ""

    def __post_init__(self) -> None:
        self.path = normalize_path(self.path)
        if not self.language:
            self.language = guess_language(self.path)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Finding:
    id: str
    title: str
    severity: str
    category: str
    file_path: str
    line: int
    evidence: str
    recommendation: str
    cwe: str = ""
    confidence: str = "medium"
    fixable: bool = False
    fix_kind: str = ""
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PatchFile:
    path: str
    original: str
    patched: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AuditResult:
    summary: dict[str, Any]
    findings: list[Finding]
    patch: str
    changed_files: list[PatchFile]
    llm: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings],
            "patch": self.patch,
            "changed_files": [patch_file.to_dict() for patch_file in self.changed_files],
            "llm": self.llm,
        }


def guess_language(path: str) -> str:
    return SUPPORTED_EXTENSIONS.get(PurePosixPath(path).suffix.lower(), "text")


def normalize_path(path: str) -> str:
    clean = path.replace("\\", "/").strip().lstrip("/")
    parts = [part for part in PurePosixPath(clean).parts if part not in ("", ".", "..")]
    return "/".join(parts) if parts else "untitled.txt"


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda item: (
            SEVERITY_ORDER.get(item.severity, 99),
            item.file_path.lower(),
            item.line,
            item.title,
        ),
    )
