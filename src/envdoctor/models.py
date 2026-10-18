from __future__ import annotations
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    key: str = ""
    path: str = ""
    line: int = 1
    suggestion: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
