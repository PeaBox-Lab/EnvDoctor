from __future__ import annotations
from pathlib import Path
from .dotenv import parse_env

def pydantic_settings(env_path: Path, class_name: str = "Settings") -> str:
    entries, _ = parse_env(env_path)
    fields = []
    for entry in dict.fromkeys(e.key for e in entries):
        fields.append(f"    {entry.lower()}: str")
    body = "\n".join(fields) or "    pass"
    return f'''from pydantic_settings import BaseSettings, SettingsConfigDict\n\nclass {class_name}(BaseSettings):\n    model_config = SettingsConfigDict(env_file=".env", extra="ignore")\n{body}\n'''
