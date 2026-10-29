# DomainWeave

A domain-agnostic, modular Agentic AI Platform built with Python, FastAPI, LangGraph, and PostgreSQL.

> **Status:** Milestone 1 — Foundation complete.  
> The platform skeleton is importable and tested. No LLM calls, database connections, or agent workflows are implemented yet.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| [uv](https://docs.astral.sh/uv/) | 0.13+ |
| Git | any recent version |

---

## Local Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd domainweave

# 2. Install all dependencies (including dev tools)
uv sync --extra dev

# 3. Create your local environment file
cp .env.example .env
# Edit .env with your local values (no secrets required for Milestone 1)
```

---

## Running the Application

```bash
# Using the console-script entry point
uv run domainweave

# Or directly with uvicorn
uv run uvicorn domainweave.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs (Swagger UI) are at `http://localhost:8000/docs` in non-production environments.

### Health check

```bash
curl http://localhost:8000/health
# {"status":"ok","app_name":"DomainWeave","version":"0.1.0","environment":"development"}
```

---

## Configuration

All settings are loaded from environment variables or a local `.env` file.  
See [`.env.example`](.env.example) for available options and their defaults.

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `DomainWeave` | Application display name |
| `ENVIRONMENT` | `development` | `development` / `testing` / `production` |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | Listen port |

---

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/unit/test_config.py -v
```

Tests require no live database, LLM provider, or external service.

---

## Linting and Formatting

```bash
# Check for lint issues
uv run ruff check src tests

# Auto-fix safe issues
uv run ruff check --fix src tests

# Format code
uv run ruff format src tests
```

---

## Project Layout

```
domainweave/
├── src/
│   └── domainweave/
│       ├── main.py          ← FastAPI app factory + entry point
│       ├── core/
│       │   ├── config.py    ← AppSettings (Pydantic Settings)
│       │   ├── logging.py   ← Centralized logging setup
│       │   └── exceptions.py← Application exception hierarchy
│       ├── api/             ← Route handlers (future milestones)
│       ├── agent/           ← Cognitive core (future milestones)
│       ├── runtime/         ← Agent runtime harness (future milestones)
│       ├── models/          ← Model Gateway (future milestones)
│       └── domains/         ← Domain Registry (future milestones)
├── configs/
│   └── domains/             ← Domain YAML configs (future milestones)
├── tests/
│   ├── conftest.py          ← Shared fixtures
│   ├── unit/                ← Pure unit tests (no I/O)
│   └── integration/         ← Integration tests (future milestones)
├── docs/
│   └── architecture.md      ← Architecture overview
├── .env.example             ← Environment variable template
├── pyproject.toml           ← Project metadata + tool config
└── README.md
```

---

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for component descriptions and responsibility boundaries.

