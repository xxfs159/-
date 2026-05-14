from __future__ import annotations

import hashlib
import re

from .models import Finding, SourceFile, sort_findings


SECRET_RE = re.compile(
    r"""(?P<prefix>\b(?P<name>password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)\b\s*[:=]\s*)(?P<quote>["'])(?P<value>[^"']{8,})(?P=quote)""",
    re.IGNORECASE,
)
SQL_FSTRING_RE = re.compile(r"""\b(execute|query)\s*\(\s*f["']""", re.IGNORECASE)
SQL_TEMPLATE_RE = re.compile(r"""\b(query|execute)\s*\(\s*`[^`]*\$\{""", re.IGNORECASE)
SQL_CONCAT_RE = re.compile(
    r"""\b(execute|query)\s*\([^;\n]*(select|insert|update|delete|where)[^;\n]*(\+|%|\.format\()""",
    re.IGNORECASE,
)
SQL_ASSIGN_RE = re.compile(
    r"""\b(?P<var>\w*sql\w*)\s*=\s*(f["'][^"']*(select|insert|update|delete|where)|["'][^"']*(select|insert|update|delete|where)[^"']*["']\s*(\+|%|\.format\())""",
    re.IGNORECASE,
)
SHELL_TRUE_RE = re.compile(r"""subprocess\.(run|call|check_output|Popen)\([^;\n]*shell\s*=\s*True""")
OS_SYSTEM_RE = re.compile(r"""\b(os\.system|os\.popen|popen|system)\s*\(""")
NODE_EXEC_RE = re.compile(r"""child_process\.(exec|execSync)\s*\(|\bexec\s*\(""")
EVAL_RE = re.compile(r"""(?<![\w.])(?:eval|exec)\s*\(""")
PICKLE_RE = re.compile(r"""\bpickle\.(load|loads)\s*\(""")
YAML_LOAD_RE = re.compile(r"""\byaml\.load\s*\(""")
WEAK_HASH_RE = re.compile(
    r"""hashlib\.(md5|sha1)\s*\(|crypto\.createHash\(\s*["'](md5|sha1)["']|MessageDigest\.getInstance\(\s*["'](MD5|SHA-1)["']""",
    re.IGNORECASE,
)
DEBUG_TRUE_RE = re.compile(r"""\b(debug\s*=\s*True|DEBUG\s*=\s*True)\b""")
CORS_WILDCARD_RE = re.compile(r"""(origins?\s*=\s*["']\*["']|Access-Control-Allow-Origin["']?\s*:\s*["']\*|CORS\(\s*app\s*\))""")
PATH_TRAVERSAL_RE = re.compile(
    r"""\b(open|send_file|send_from_directory|FileInputStream|readFileSync)\s*\([^;\n]*(request\.|req\.|params|query|body|args|getParameter)""",
    re.IGNORECASE,
)
SSRF_RE = re.compile(
    r"""\b(requests\.(get|post|put|delete)|urllib\.request\.urlopen|axios\.(get|post)|fetch)\s*\([^;\n]*(request\.|req\.|params|query|body|args|getParameter|location\.)""",
    re.IGNORECASE,
)
XSS_RE = re.compile(
    r"""(\.innerHTML\s*=|dangerouslySetInnerHTML|document\.write\s*\()[^;\n]*(request\.|req\.|params|query|body|args|location\.)?""",
    re.IGNORECASE,
)


def scan_files(files: list[SourceFile], max_findings: int = 200) -> list[Finding]:
    findings: list[Finding] = []
    for source_file in files:
        if source_file.language == "text":
            continue
        findings.extend(scan_file(source_file))
        if len(findings) >= max_findings:
            break
    return sort_findings(findings[:max_findings])


def scan_file(source_file: SourceFile) -> list[Finding]:
    findings: list[Finding] = []
    lines = source_file.content.splitlines()

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "*")):
            continue

        secret_match = SECRET_RE.search(line)
        if secret_match and _looks_like_real_secret(secret_match.group("value")):
            findings.append(
                _finding(
                    "Hardcoded credential",
                    "high",
                    "Secrets",
                    source_file.path,
                    index,
                    line,
                    "Move the secret to environment variables or a managed secret store, then rotate the exposed value.",
                    cwe="CWE-798",
                    fixable=True,
                    fix_kind="hardcoded_secret",
                )
            )

        if (
            SQL_FSTRING_RE.search(line)
            or SQL_TEMPLATE_RE.search(line)
            or SQL_CONCAT_RE.search(line)
            or SQL_ASSIGN_RE.search(line)
        ):
            findings.append(
                _finding(
                    "Possible SQL injection",
                    "critical",
                    "Injection",
                    source_file.path,
                    index,
                    line,
                    "Use parameterized queries or prepared statements; never concatenate request-controlled data into SQL.",
                    cwe="CWE-89",
                )
            )

        if SHELL_TRUE_RE.search(line) or OS_SYSTEM_RE.search(line) or NODE_EXEC_RE.search(line):
            findings.append(
                _finding(
                    "Possible command injection",
                    "critical",
                    "Injection",
                    source_file.path,
                    index,
                    line,
                    "Avoid shell execution. Pass an argument list to subprocess APIs and validate allowlisted commands.",
                    cwe="CWE-78",
                )
            )

        if EVAL_RE.search(line):
            findings.append(
                _finding(
                    "Dynamic code execution",
                    "high",
                    "Unsafe evaluation",
                    source_file.path,
                    index,
                    line,
                    "Replace eval/exec with explicit parsers, dispatch tables, or safe expression evaluators.",
                    cwe="CWE-95",
                )
            )

        if PICKLE_RE.search(line):
            findings.append(
                _finding(
                    "Unsafe deserialization",
                    "high",
                    "Deserialization",
                    source_file.path,
                    index,
                    line,
                    "Do not unpickle untrusted data. Use JSON or a signed, schema-validated format.",
                    cwe="CWE-502",
                )
            )

        if YAML_LOAD_RE.search(line) and "SafeLoader" not in line and "safe_load" not in line:
            findings.append(
                _finding(
                    "Unsafe YAML load",
                    "high",
                    "Deserialization",
                    source_file.path,
                    index,
                    line,
                    "Use yaml.safe_load or yaml.load(..., Loader=yaml.SafeLoader) for untrusted YAML.",
                    cwe="CWE-502",
                    fixable=True,
                    fix_kind="yaml_safe_load",
                )
            )

        if WEAK_HASH_RE.search(line):
            findings.append(
                _finding(
                    "Weak cryptographic hash",
                    "medium",
                    "Cryptography",
                    source_file.path,
                    index,
                    line,
                    "Use SHA-256 or stronger for integrity checks; use password hashing such as Argon2/bcrypt for passwords.",
                    cwe="CWE-327",
                    fixable=True,
                    fix_kind="weak_hash",
                )
            )

        if DEBUG_TRUE_RE.search(line):
            findings.append(
                _finding(
                    "Debug mode enabled",
                    "medium",
                    "Configuration",
                    source_file.path,
                    index,
                    line,
                    "Disable debug mode in production and move runtime mode to environment-specific configuration.",
                    cwe="CWE-489",
                    fixable=True,
                    fix_kind="debug_true",
                )
            )

        if CORS_WILDCARD_RE.search(line):
            findings.append(
                _finding(
                    "Overly broad CORS policy",
                    "medium",
                    "Configuration",
                    source_file.path,
                    index,
                    line,
                    "Restrict CORS origins to known trusted domains and avoid wildcard access for credentialed endpoints.",
                    cwe="CWE-942",
                )
            )

        if PATH_TRAVERSAL_RE.search(line):
            findings.append(
                _finding(
                    "Possible path traversal",
                    "high",
                    "File access",
                    source_file.path,
                    index,
                    line,
                    "Normalize the path, reject traversal segments, and resolve it inside an allowlisted base directory.",
                    cwe="CWE-22",
                )
            )

        if SSRF_RE.search(line):
            findings.append(
                _finding(
                    "Possible SSRF sink",
                    "high",
                    "Network access",
                    source_file.path,
                    index,
                    line,
                    "Validate target hosts against an allowlist and block private/link-local network ranges.",
                    cwe="CWE-918",
                )
            )

        if XSS_RE.search(line):
            findings.append(
                _finding(
                    "Possible DOM XSS",
                    "medium",
                    "Cross-site scripting",
                    source_file.path,
                    index,
                    line,
                    "Render untrusted values as text, sanitize HTML with a proven sanitizer, or encode output by context.",
                    cwe="CWE-79",
                )
            )

    return _deduplicate(findings)


def _finding(
    title: str,
    severity: str,
    category: str,
    file_path: str,
    line: int,
    evidence: str,
    recommendation: str,
    *,
    cwe: str = "",
    fixable: bool = False,
    fix_kind: str = "",
) -> Finding:
    fingerprint = hashlib.sha1(f"{title}:{file_path}:{line}:{evidence.strip()}".encode("utf-8")).hexdigest()[:10]
    return Finding(
        id=f"F-{fingerprint}",
        title=title,
        severity=severity,
        category=category,
        file_path=file_path,
        line=line,
        evidence=evidence.strip(),
        recommendation=recommendation,
        cwe=cwe,
        fixable=fixable,
        fix_kind=fix_kind,
    )


def _looks_like_real_secret(value: str) -> bool:
    lowered = value.lower()
    placeholders = ("example", "changeme", "replace", "dummy", "sample", "test", "todo", "your_")
    if any(token in lowered for token in placeholders):
        return False
    if lowered.startswith(("http://", "https://")):
        return False
    return len(set(value)) >= 5


def _deduplicate(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, int]] = set()
    unique: list[Finding] = []
    for finding in findings:
        key = (finding.title, finding.file_path, finding.line)
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique
