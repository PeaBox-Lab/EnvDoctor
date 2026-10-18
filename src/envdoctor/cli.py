from __future__ import annotations
import argparse
from pathlib import Path
import sys
from .generator import pydantic_settings
from .reporters import html_report, json_report, sarif_report
from .scanner import scan


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="envdoctor", description="Diagnose environment-variable configuration drift without printing secret values.")
    p.add_argument("--version", action="version", version="EnvDoctor 0.1.0")
    sub = p.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Scan a project and print findings")
    check.add_argument("path", nargs="?", default=".")
    check.add_argument("--env", default=".env", dest="env_file")
    check.add_argument("--example", default=".env.example", dest="example_file")
    check.add_argument("--format", choices=("text", "json", "sarif", "html"), default="text")
    check.add_argument("--output", "-o")
    check.add_argument("--fail-on", choices=("error", "warning", "never"), default="error")
    gen = sub.add_parser("generate", help="Generate a Pydantic settings model")
    gen.add_argument("--env", default=".env", dest="env_file")
    gen.add_argument("--output", "-o", default="settings.py")
    gen.add_argument("--class-name", default="Settings")
    return p


def text_report(findings, summary) -> str:
    lines = ["EnvDoctor 0.1.0", f"Defined: {summary['defined']}  Referenced: {summary['referenced']}  Errors: {summary['findings']['error']}  Warnings: {summary['findings']['warning']}", ""]
    for f in findings:
        location = f"{f.path}:{f.line}" if f.path else "project"
        lines.append(f"[{f.severity.upper():7}] {f.rule_id} {location} {f.key} - {f.message}")
        if f.suggestion:
            lines.append(f"          Fix: {f.suggestion}")
    if not findings:
        lines.append("OK: no findings")
    return "\n".join(lines)


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    if args.command == "generate":
        Path(args.output).write_text(pydantic_settings(Path(args.env_file), args.class_name), encoding="utf-8")
        print(f"Generated {args.output}")
        return 0
    root = Path(args.path).resolve()
    env_path = (root / args.env_file) if not Path(args.env_file).is_absolute() else Path(args.env_file)
    example_path = (root / args.example_file) if args.example_file and not Path(args.example_file).is_absolute() else (Path(args.example_file) if args.example_file else None)
    if example_path and not example_path.exists():
        example_path = None
    findings, summary = scan(root, env_path, example_path)
    output = {"text": text_report(findings, summary), "json": json_report(findings, summary), "sarif": sarif_report(findings), "html": html_report(findings, summary)}[args.format]
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(output)
    severities = {f.severity for f in findings}
    return int(args.fail_on == "error" and "error" in severities or args.fail_on == "warning" and bool(severities & {"error", "warning"}))

if __name__ == "__main__":
    sys.exit(main())
