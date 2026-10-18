from pathlib import Path
from envdoctor.dotenv import parse_env
from envdoctor.scanner import scan
from envdoctor.reporters import sarif_report


def test_parse_and_duplicate(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("PORT=8000\nPORT=9000\n", encoding="utf-8")
    entries, errors = parse_env(p)
    assert not errors and len(entries) == 2


def test_missing_unused_and_secret_redaction(tmp_path: Path):
    (tmp_path / "app.py").write_text('import os\nprint(os.getenv("DATABASE_URL"))\n', encoding="utf-8")
    env = tmp_path / ".env"
    env.write_text("UNUSED=x\nAPI_KEY=sk_live_abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
    findings, summary = scan(tmp_path, env)
    ids = {f.rule_id for f in findings}
    assert {"ENV101", "ENV201", "ENV401"} <= ids
    serialized = sarif_report(findings)
    assert "sk_live" not in serialized
    assert summary["findings"]["error"] >= 2
