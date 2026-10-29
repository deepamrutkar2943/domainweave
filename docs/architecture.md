# DomainWeave — Architecture

> **Milestone status:** This document describes the boundaries of all planned components.  
> Sections marked **✅ Implemented** reflect working, tested code.  
> Sections marked **🔲 Planned** describe the intended design; no code exists yet.

---

## Overview

DomainWeave is a domain-agnostic Agentic AI Platform organized as a modular monolith. Each component has a distinct responsibility boundary. Components communicate through well-defined Python interfaces — not through shared mutable state or direct cross-component database queries.

```
User / External Client
        │
        ▼
┌───────────────┐
│   API Layer   │  FastAPI — HTTP only, no orchestration logic
└──────┬────────┘
       │
       ▼
┌───────────────────┐
│  Agent Runtime /  │  Lifecycle manager — loads domain, invokes graph
│    Harness        │
└──────┬────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│                  Cognitive Core                     │
│  Intent Analyzer → Router → Capability Selector    │
│  → Planner → Evidence Evaluator → Outcome Eval     │
│  → Response Synthesizer                            │
└──────┬──────────────────────────────────────────────┘
       │
   ┌───┴────────────────────────────────────┐
   │                                        │
   ▼                                        ▼
┌────────────────┐                ┌──────────────────────┐
│  Model Gateway │                │  Tool Registry &     │
│                │                │  Executor            │
└────────────────┘                └──────────────────────┘
       │                                   │
       ▼                                   ▼
┌────────────────┐                ┌──────────────────────┐
│  Domain        │                │  Application Services│
│  Registry      │                │  & Repositories      │
└────────────────┘                └──────────────────────┘
                                           │
                                           ▼
                                  ┌──────────────────────┐
                                  │  PostgreSQL           │
                                  │  (app data + pgvector)│
                                  └──────────────────────┘
```

---

## Components

### ✅ A. API Layer (`src/domainweave/api/`)

**Implemented:** `/health` endpoint.

**Responsibilities:**
- Expose versioned REST endpoints.
- Validate requests and responses using Pydantic.
- Integrate with authentication and authorization (future).
- Initiate agent runs and retrieve results (future).
- Return consistent errors and status codes.

FastAPI owns HTTP concerns only. Agent orchestration must not live in route handlers.

---

### 🔲 B. Agent Runtime / Harness (`src/domainweave/runtime/`)

**Responsibilities:**
- Manage the lifecycle of a single agent run.
- Establish a trusted execution context.
- Resolve the active domain configuration.
- Initialize LangGraph state and invoke the workflow.
- Handle completed, failed, interrupted, and approval-required outcomes.
- Normalize workflow results for the API layer.

This is a thin coordinator. LangGraph executes the workflow; the runtime manages the application lifecycle around it.

---

### 🔲 C. Cognitive Core (`src/domainweave/agent/`)

Logical responsibilities (implemented as Python functions / LangGraph nodes):

| Sub-component | Responsibility |
|---|---|
| Intent & Task Analyzer | Interpret requests, extract entities, detect ambiguity |
| Router | Select workflow via deterministic conditional edges |
| Capability Selector | Pick approved capabilities from the catalog |
| Planner | Build structured multi-step plans (when needed) |
| Evidence Evaluator | Assess whether evidence supports a conclusion |
| Outcome Evaluator | Determine whether completion criteria are met |
| Response Synthesizer | Produce grounded, cited, schema-validated responses |

These are not separate agents. They are ordinary Python functions exposed as LangGraph nodes.

---

### 🔲 D. Model Gateway (`src/domainweave/models/`)

**Responsibilities:**
- Resolve approved logical model profiles (`classification`, `general_response`, `reasoning`, `embedding`).
- Create or reuse provider-specific clients.
- Isolate all provider credentials and URLs.
- Normalize provider errors and collect usage metrics.
- Enforce model-call and cost limits.

Business logic must not import provider SDKs directly.

---

### 🔲 E. Domain Registry (`src/domainweave/domains/`)

**Responsibilities:**
- Load and validate domain YAML configurations from `configs/domains/`.
- Expose the active domain's permitted model profiles, enabled capabilities, knowledge collections, and policies.
- Ensure adding a new domain requires only a configuration file — not a code change.

---

### 🔲 F. Tool Registry and Executor

**Responsibilities:**
- Maintain a catalog of approved tools with stable identifiers, argument schemas, permission requirements, and execution handlers.
- Validate all tool calls against the catalog before execution.
- Enforce timeout, retry, and idempotency requirements.
- The model proposes tool calls; application code controls execution.

---

### 🔲 G. Policy Engine and Authorization

**Responsibilities:**
- Authenticate principals (identity verification).
- Authorize actions against resources (permission checks).
- Evaluate domain-specific business rules.

Authorization is enforced at protected service/execution boundaries — not inside LLM prompts.

---

### 🔲 H. Knowledge Service and RAG

**Responsibilities:**
- Ingest documents (PDF, text), chunk, embed, and store in PostgreSQL + pgvector.
- Hybrid retrieval: semantic (pgvector) + keyword (PostgreSQL full-text search).
- Apply domain, tenant, and document-permission filters on every query.
- Return structured evidence with citations.

Retrieved document text is treated as untrusted input.

---

### 🔲 I. Application Services and Repositories

Pattern:

```
Tool definition → Tool Executor → Application Service → Repository / External adapter
```

Business operations remain callable from REST endpoints without requiring an LLM invocation.

---

### 🔲 J. Persistence and Checkpointing

| Data category | Storage |
|---|---|
| Application and domain data | PostgreSQL via SQLAlchemy / Alembic |
| Conversation and run metadata | PostgreSQL |
| Knowledge documents and vectors | PostgreSQL + pgvector |
| LangGraph execution checkpoints | PostgreSQL LangGraph checkpointer |
| Audit records | PostgreSQL (separate table, append-only) |

Checkpointing is a recovery mechanism, not unlimited memory.

---

### 🔲 K. Observability and Evaluation

- **LangSmith:** LLM and workflow tracing.
- **Structured logging:** `src/domainweave/core/logging.py` — implemented in Milestone 1.
- **Audit records:** Separate append-only table for security and business events.
- **Evaluation dataset:** Fixed dataset covering routing, tool selection, retrieval, citations, policy compliance.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Package layout | `src`-based | Prevents accidental imports from the project root |
| Settings | Pydantic Settings | Validated, typed, env-var-driven config |
| Orchestration | LangGraph | Explicit graph-based control flow, built-in checkpointing |
| HTTP framework | FastAPI | Async, Pydantic-native, auto-docs |
| Persistence | PostgreSQL + pgvector | Single engine for app data and vector search |
| Dependency management | `uv` | Fast, lockfile-reproducible |
| Linting | Ruff | Fast, single-tool replacement for flake8 + isort |

---

## Implemented vs. Planned

| Component | Status |
|---|---|
| Package skeleton | ✅ Milestone 1 |
| AppSettings + .env loading | ✅ Milestone 1 |
| Centralized logging | ✅ Milestone 1 |
| Exception hierarchy | ✅ Milestone 1 |
| FastAPI app + /health | ✅ Milestone 1 |
| Domain Registry | 🔲 Milestone 2 |
| Model Gateway | 🔲 Milestone 2 |
| Cognitive Core + LangGraph workflow | 🔲 Milestone 3 |
| Tool Registry and Executor | 🔲 Milestone 4 |
| Policy Engine | 🔲 Milestone 4 |
| PostgreSQL + pgvector + RAG | 🔲 Milestone 5 |
| Planning + Outcome Evaluation | 🔲 Milestone 6 |
| Checkpointing + Audit | 🔲 Milestone 7 |
| Evaluation suite | 🔲 Milestone 8 |
| Docker + CI | 🔲 Milestone 9 |

