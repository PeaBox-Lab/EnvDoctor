from __future__ import annotations
from collections import Counter
from pathlib import Path
import math
import re
from .dotenv import parse_env
from .models import Finding

IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".mypy_cache", ".pytest_cache"}
TEXT_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".rb", ".php", ".sh", ".yml", ".yaml", ".toml", ".json"}
REFERENCE_PATTERNS = [
    re.compile(r"(?:os\.environ\[['\"]|os\.getenv\(['\"]|getenv\(['\"])([A-Z][A-Z0-9_]*)"),
    re.compile(r"(?:process\.env\.|import\.meta\.env\.)([A-Z][A-Z0-9_]*)"),
    re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}"),
    re.compile(r"env\(['\"]([A-Z][A-Z0-9_]*)"),
]
PLACEHOLDERS = {"", "changeme", "change-me", "replace-me", "todo", "example", "your-value", "xxx"}
SENSITIVE_WORDS = ("SECRET", "TOKEN", "PASSWORD", "PASSWD", "PRIVATE_KEY", "API_KEY", "ACCESS_KEY")


def entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    return -sum((n / len(value)) * math.log2(n / len(value)) for n in counts.values())


def iter_source_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and not any(part in IGNORE_DIRS for part in path.parts):
            try:
                if path.stat().st_size <= 2_000_000:
                    yield path
            except OSError:
                continue


def find_references(root: Path) -> dict[str, list[tuple[str, int]]]:
    refs: dict[str, list[tuple[str, int]]] = {}
    for path in iter_source_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, 1):
            for pattern in REFERENCE_PATTERNS:
                for match in pattern.finditer(line):
                    refs.setdefault(match.group(1), []).append((str(path.relative_to(root)), line_no))
    return refs


def scan(root: Path, env_path: Path, example_path: Path | None = None) -> tuple[list[Finding], dict]:
    env_entries, syntax_errors = parse_env(env_path)
    example_entries, example_errors = parse_env(example_path) if example_path else ([], [])
    refs = find_references(root)
    findings: list[Finding] = []
    for line, msg in syntax_errors:
        findings.append(Finding("ENV001", "error", msg, path=str(env_path), line=line))
    if example_path:
        for line, msg in example_errors:
            findings.append(Finding("ENV001", "error", msg, path=str(example_path), line=line))
    counts = Counter(e.key for e in env_entries)
    for entry in env_entries:
        if counts[entry.key] > 1:
            findings.append(Finding("ENV002", "error", "Duplicate key in environment file", entry.key, str(env_path), entry.line, "Keep one authoritative definition."))
    actual = {e.key: e for e in env_entries}
    example = {e.key: e for e in example_entries}
    for key, locations in sorted(refs.items()):
        if key not in actual:
            path, line = locations[0]
            findings.append(Finding("ENV101", "error", "Referenced variable is missing from the selected environment file", key, path, line, f"Add {key}=... to {env_path.name}."))
        if example_path and key not in example:
            path, line = locations[0]
            findings.append(Finding("ENV102", "warning", "Referenced variable is missing from the example file", key, path, line, f"Document {key} in {example_path.name}."))
    for key, entry in sorted(actual.items()):
        if key not in refs:
            findings.append(Finding("ENV201", "warning", "Variable is defined but no supported source-code reference was found", key, str(env_path), entry.line, "Remove it or add it to the ignore list if consumed externally."))
        low = entry.value.strip().lower()
        if low in PLACEHOLDERS:
            findings.append(Finding("ENV301", "warning", "Value is empty or appears to be a placeholder", key, str(env_path), entry.line, "Set a real runtime value outside version control."))
        if any(word in key.upper() for word in SENSITIVE_WORDS) and len(entry.value) >= 12 and entropy(entry.value) >= 3.2:
            findings.append(Finding("ENV401", "error", "Potential secret detected; value has been redacted", key, str(env_path), entry.line, "Rotate the credential if committed, remove it from Git history, and use a secret manager."))
    if example_path:
        for key, entry in sorted(example.items()):
            if key not in actual:
                findings.append(Finding("ENV202", "info", "Example variable is not present in the selected environment file", key, str(example_path), entry.line))
    summary = {
        "root": str(root), "env_file": str(env_path), "example_file": str(example_path) if example_path else None,
        "defined": len(actual), "referenced": len(refs),
        "findings": {level: sum(f.severity == level for f in findings) for level in ("error", "warning", "info")},
    }
    return findings, summary
