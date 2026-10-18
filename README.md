# EnvDoctor

> Diagnose environment-variable drift before configuration breaks production.

EnvDoctor is a local-first Python CLI that compares environment files with variables referenced by source code. It detects missing, duplicated, undocumented, unused, placeholder, and potentially sensitive values without printing secret contents.

## What v0.1 does

- Parses `.env` and `.env.example` files
- Finds common references in Python, JavaScript, TypeScript, shell, YAML, JSON, Go, Rust, Java, Ruby, and PHP projects
- Reports missing variables and `.env.example` drift
- Flags duplicate keys, placeholders, unused variables, and likely secrets
- Redacts all values from console and generated reports
- Exports text, JSON, HTML, and SARIF 2.1.0
- Generates a starter `pydantic-settings` model
- Returns CI-friendly exit codes
- Includes tests and GitHub Actions workflows

## Install from source

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -e .
# macOS/Linux:
.venv/bin/python -m pip install -e .
```

## Use

```bash
envdoctor check .
envdoctor check . --env .env.local --example .env.example
envdoctor check . --format json -o envdoctor.json
envdoctor check . --format html -o envdoctor.html
envdoctor check . --format sarif -o envdoctor.sarif
envdoctor generate --env .env.example -o settings.py
```

Run the included intentionally unhealthy example:

```bash
envdoctor check examples --env .env --example .env.example --fail-on never
envdoctor check examples --env .env --example .env.example --format html -o report.html --fail-on never
```

## Rules

| Rule | Meaning | Default severity |
|---|---|---|
| ENV001 | Invalid dotenv syntax | Error |
| ENV002 | Duplicate key | Error |
| ENV101 | Referenced key missing from selected env file | Error |
| ENV102 | Referenced key missing from example contract | Warning |
| ENV201 | Defined key has no detected source reference | Warning |
| ENV202 | Example key not present in selected env file | Info |
| ENV301 | Empty or placeholder-like value | Warning |
| ENV401 | Potential secret value detected | Error |

## Safety choices

EnvDoctor never includes environment values in findings or reports. Secret detection is intentionally conservative and uses key names, value length, and entropy. A finding is a prompt to investigate, not proof that a credential is valid.

## Known v0.1 limits

- Static pattern matching cannot see every framework-specific configuration mechanism.
- Variables consumed only by cloud platforms, Docker, deployment manifests, or external systems can appear unused.
- Multiline dotenv values and shell interpolation are parsed conservatively.
- Secret detection can produce false positives and does not replace a dedicated secret scanner.

## Developer setup

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python -m build
```

## Roadmap

- Ignore/config file (`envdoctor.toml`)
- Framework adapters for Django, FastAPI, Next.js, Vite, Docker Compose, and Kubernetes
- Typed schema inference and interactive repair
- Monorepo workspaces and environment profiles
- Git history checking through a dedicated secret-scanner adapter
- Desktop UI

## License

MIT
