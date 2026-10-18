from __future__ import annotations
from html import escape
import json
from .models import Finding


def json_report(findings: list[Finding], summary: dict) -> str:
    return json.dumps({"tool": "EnvDoctor", "version": "0.1.0", "summary": summary, "findings": [f.to_dict() for f in findings]}, indent=2)


def sarif_report(findings: list[Finding]) -> str:
    rules = {}
    for f in findings:
        rules.setdefault(f.rule_id, {"id": f.rule_id, "shortDescription": {"text": f.message}})
    level = {"error": "error", "warning": "warning", "info": "note"}
    results = []
    for f in findings:
        item = {"ruleId": f.rule_id, "level": level[f.severity], "message": {"text": f"{f.key + ': ' if f.key else ''}{f.message}"}}
        if f.path:
            item["locations"] = [{"physicalLocation": {"artifactLocation": {"uri": f.path.replace('\\', '/')}, "region": {"startLine": max(1, f.line)}}}]
        results.append(item)
    data = {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": [{"tool": {"driver": {"name": "EnvDoctor", "version": "0.1.0", "rules": list(rules.values())}}, "results": results}]}
    return json.dumps(data, indent=2)


def html_report(findings: list[Finding], summary: dict) -> str:
    rows = "".join(f"<tr><td><span class='{f.severity}'>{escape(f.severity)}</span></td><td>{escape(f.rule_id)}</td><td><b>{escape(f.key)}</b><br>{escape(f.message)}</td><td>{escape(f.path)}:{f.line}</td><td>{escape(f.suggestion)}</td></tr>" for f in findings)
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>EnvDoctor report</title><style>body{{font:15px system-ui;margin:40px;background:#f6f8fb;color:#18202a}}main{{max-width:1200px;margin:auto}}.cards{{display:flex;gap:12px}}.card,table{{background:white;border-radius:12px;box-shadow:0 4px 18px #0001}}.card{{padding:18px;min-width:130px}}table{{width:100%;border-collapse:collapse;margin-top:20px;overflow:hidden}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #e8ebef;vertical-align:top}}th{{background:#102a43;color:white}}span{{padding:3px 8px;border-radius:20px;font-weight:700}}.error{{background:#fee2e2;color:#991b1b}}.warning{{background:#fef3c7;color:#92400e}}.info{{background:#dbeafe;color:#1e40af}}</style></head><body><main><h1>EnvDoctor</h1><p>Environment configuration health report. Secret values are never included.</p><div class='cards'><div class='card'><b>Defined</b><h2>{summary['defined']}</h2></div><div class='card'><b>Referenced</b><h2>{summary['referenced']}</h2></div><div class='card'><b>Errors</b><h2>{summary['findings']['error']}</h2></div><div class='card'><b>Warnings</b><h2>{summary['findings']['warning']}</h2></div></div><table><thead><tr><th>Severity</th><th>Rule</th><th>Finding</th><th>Location</th><th>Suggested action</th></tr></thead><tbody>{rows or '<tr><td colspan=5>No findings. Environment configuration looks healthy.</td></tr>'}</tbody></table></main></body></html>"""
