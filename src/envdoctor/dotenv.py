from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

@dataclass(frozen=True)
class EnvEntry:
    key: str
    value: str
    line: int
    exported: bool = False


def parse_env(path: Path) -> tuple[list[EnvEntry], list[tuple[int, str]]]:
    entries: list[EnvEntry] = []
    errors: list[tuple[int, str]] = []
    if not path.exists():
        return entries, errors
    for number, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        exported = False
        if text.startswith("export "):
            exported, text = True, text[7:].lstrip()
        if "=" not in text:
            errors.append((number, "Expected KEY=VALUE"))
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        if not KEY_RE.match(key):
            errors.append((number, f"Invalid environment variable name: {key!r}"))
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        entries.append(EnvEntry(key, value, number, exported))
    return entries, errors
