# Architecture Walkthrough

## System Summary

This project behaves like a tiny LLM tracing system:

- an application sends a prompt
- the backend forwards it to Groq
- the backend measures performance and usage
- the trace is stored in a database
- the frontend renders the trace history
- users attach quality feedback

## Core Components

### 1. API Layer

FastAPI receives requests, validates payloads, and exposes trace endpoints.

### 2. Provider Layer

`GroqClient` is responsible for calling the model provider and extracting response metadata.

### 3. Observability Layer

`ObservabilityService` translates model activity into persistent traces.

### 4. Persistence Layer

SQLAlchemy stores each trace as an `LLMLog`.

### 5. Presentation Layer

Next.js fetches traces and metrics and renders them in a dashboard.

## Why This Design Is Interview-Friendly

- simple enough to finish
- clean enough to defend architecturally
- practical enough to demonstrate LLM engineering maturity

## Production Upgrade Path

- Replace SQLite with PostgreSQL.
- Add Alembic migrations.
- Add auth and multi-project scoping.
- Add background analytics jobs.
- Add prompt tags, trace ids, sessions, and costs.
- Export metrics to Prometheus or OpenTelemetry.

