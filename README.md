# Mini Langfuse Reimplementation 

This project is a focused reimplementation of Langfuse's core ideas:

- hierarchical observability with `trace -> span -> generation`
- score-based evaluation
- prompt template versioning
- analytics and filtering
- an NLP evaluation layer for semantic similarity, classifier scores, and LLM-as-judge

It is intentionally smaller than the real Langfuse product, but the architecture is much closer to the real platform than a single logging table.

## Stack

- Backend: FastAPI + SQLAlchemy
- Frontend: Next.js App Router
- Database: SQLite by default, PostgreSQL-ready through `DATABASE_URL`
- LLM provider: Groq
- NLP layer: `sentence-transformers`, `transformers`, `tiktoken` with graceful fallback behavior

## Architecture

### Core data model

```text
Trace
  └── Span
       └── Generation
Trace
  └── Scores
PromptTemplate
```

### Tables

- `traces`: one user-visible request or workflow execution
- `spans`: nested pipeline steps such as generation, retrieval, embedding
- `generations`: concrete LLM calls with latency, tokens, cost, model, prompt, response
- `scores`: unified evaluation storage for human, model-based, and LLM-as-judge metrics
- `prompt_templates`: versioned prompt definitions with labels such as `staging` and `production`

## Folder structure

```text
backend/
  app/
    api/routes.py
    core/config.py
    db/session.py
    models/
      trace.py
      span.py
      generation.py
      score.py
      prompt_template.py
    schemas/observability.py
    sdk/client.py
    services/
      evaluation_service.py
      groq_client.py
      llm_observer.py
      observability_service.py
      token_counter.py
    main.py
frontend/
  app/
    components/
      AnalyticsPanel.tsx
      FeedbackButtons.tsx
      PlaygroundPanel.tsx
      PromptManager.tsx
      PromptPanel.tsx
      ScoreFilterPanel.tsx
      StatsCards.tsx
      TraceDetail.tsx
      TraceTable.tsx
    lib/
      api.ts
      types.ts
    globals.css
    layout.tsx
    page.tsx
README.md
ARCHITECTURE.md
INTERVIEW_PREP.md
```

## What each backend file does

### `backend/app/main.py`

Creates the FastAPI app, initializes database tables, and configures CORS.

### `backend/app/core/config.py`

Loads environment variables for:

- Groq API key and models
- DB connection
- CORS origins
- evaluation flags

### `backend/app/db/session.py`

Creates the SQLAlchemy engine, session factory, and request-scoped DB dependency.

### `backend/app/models/*.py`

Defines the relational schema:

- `trace.py`: root request unit
- `span.py`: nested operations inside a trace
- `generation.py`: actual LLM calls with observability metadata
- `score.py`: polymorphic scores
- `prompt_template.py`: versioned prompts

### `backend/app/schemas/observability.py`

Pydantic request and response models for traces, prompts, scores, analytics, and playground comparison.

### `backend/app/services/groq_client.py`

Encapsulates Groq API calls.

Important observability responsibilities:

- measure latency around provider calls
- read provider token counts when available
- fall back to local counting if needed
- estimate per-generation cost

### `backend/app/services/token_counter.py`

Provides deterministic token counting with `tiktoken` when available and a fallback estimator when not.

### `backend/app/services/evaluation_service.py`

Runs the NLP layer:

- semantic similarity via `sentence-transformers`
- zero-shot scoring via `transformers`
- LLM-as-judge in a background task

### `backend/app/services/observability_service.py`

Owns persistence and analytics logic:

- create traces, spans, generations, scores
- fetch trace detail
- aggregate dashboard metrics
- manage prompt templates
- filter traces by score

### `backend/app/services/llm_observer.py`

This is the core logging wrapper.

Every generation request flows through this class so:

- logging is consistent
- latency tracking is automatic
- token tracking is automatic
- scores are attached centrally

### `backend/app/sdk/client.py`

A lightweight Python SDK wrapper showing how another app could instrument itself against this backend.

## API surface

### Tracing

- `POST /api/traces/generate`
- `POST /api/chat`
- `GET /api/traces`
- `GET /api/traces/{trace_id}`
- `POST /api/traces/{trace_id}/feedback`

### Scores and analytics

- `GET /api/scores`
- `GET /api/scores/filter`
- `GET /api/analytics/overview`

### Prompt management

- `GET /api/prompts`
- `POST /api/prompts`
- `POST /api/prompts/{name}`
- `GET /api/prompts/{name}/production`
- `PUT /api/prompts/{name}/{version}/label`
- `GET /api/prompts/{name}/metrics`

### Playground

- `POST /api/playground/compare`

## End-to-end data flow

1. A client submits a prompt to `POST /api/traces/generate`.
2. `LLMObserver` creates a `Trace`.
3. It creates a generation `Span`.
4. `GroqClient` calls the LLM provider and measures latency.
5. Tokens and cost are computed.
6. A `Generation` row is stored.
7. NLP evaluation runs:
   - semantic similarity
   - classifier scores
   - background LLM-as-judge
8. All scores are stored in `scores`.
9. The dashboard fetches traces, analytics, prompts, and score filters.

## How to run locally

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set your Groq key in `backend/.env`, then run:

```powershell
uvicorn app.main:app --reload
```

Backend docs:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Frontend

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Frontend:

- [http://localhost:3000](http://localhost:3000)

## Example request

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/api/traces/generate `
  -ContentType "application/json" `
  -Body '{"name":"demo-trace","input":"Explain retrieval augmented generation in 3 bullets","session_id":"session-1"}'
```

## What makes this Langfuse-like

- hierarchical traces instead of a flat log table
- polymorphic scores table
- prompt versioning and production labels
- analytics and score-based filtering
- an SDK-style instrumentation entry point

## What makes this stronger for an NLP / Transformers interview

- semantic similarity scoring
- zero-shot classifier outputs saved as scores
- LLM-as-judge metrics stored in the same score model

## Production upgrades

- move from SQLite to PostgreSQL
- add Alembic migrations
- add auth and project isolation
- add pagination and richer filtering
- add retrieval / embedding spans
- add OpenTelemetry export
- add dataset runs and experiments

