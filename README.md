# Mini Langfuse Clone for Interview Prep

This project is a simplified, production-style reimplementation of the core Langfuse idea: observe and analyze LLM calls.

It logs:

- prompt
- response
- model name
- latency
- token usage
- user feedback

The stack is intentionally interview-friendly:

- Backend: FastAPI
- Frontend: Next.js
- Database: SQLite by default, PostgreSQL-ready through `DATABASE_URL`
- LLM provider: Groq API with LLaMA 3.1

## 1. Folder Structure

```text
mini-langfuse-clone/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── db/
│   │   │   └── session.py
│   │   ├── models/
│   │   │   └── llm_log.py
│   │   ├── schemas/
│   │   │   └── llm_log.py
│   │   ├── services/
│   │   │   ├── groq_client.py
│   │   │   ├── llm_observer.py
│   │   │   ├── observability_service.py
│   │   │   └── token_counter.py
│   │   └── main.py
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   ├── FeedbackButtons.tsx
│   │   │   ├── LogsTable.tsx
│   │   │   └── StatsCards.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── .env.local.example
│   ├── next-env.d.ts
│   ├── next.config.mjs
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## 2. Architecture Overview

There are three main layers:

1. Frontend dashboard
2. FastAPI backend
3. Database + external LLM provider

### Why this architecture works

- The frontend only focuses on presentation and actions like feedback submission.
- The backend owns business logic, observability, provider calls, and persistence.
- The database stores traces so you can inspect past behavior.
- The Groq integration is isolated in a service class so providers can be swapped later.

This separation is exactly what interviewers want to see: clean boundaries, testability, and easy extensibility.

## 3. End-to-End Data Flow

Here is the request flow:

1. A user sends a prompt to `POST /api/chat`.
2. FastAPI validates the request with Pydantic.
3. The backend calls the Groq API through `GroqClient`.
4. The client measures latency around the API call.
5. The backend extracts token usage from Groq if available.
6. If usage is missing, it estimates tokens locally.
7. The backend stores the full trace in the `llm_logs` table.
8. The API returns the response plus observability metadata.
9. The Next.js dashboard calls `GET /api/logs` and `GET /api/stats`.
10. The user can submit thumbs up/down with `POST /api/logs/{id}/feedback`.

That is the simplified Langfuse pattern: capture inference events, enrich them with telemetry, persist them, and expose them in a dashboard.

## 4. Backend File-by-File Explanation

### `backend/app/main.py`

This is the FastAPI entry point.

It does three things:

- creates the FastAPI app
- creates database tables on startup
- enables CORS so the Next.js frontend can call the backend

### `backend/app/core/config.py`

This centralizes environment configuration:

- Groq API key
- default model
- database URL
- CORS origins

Why needed:
You want configuration outside code so the same app can run locally, in staging, or in production.

### `backend/app/db/session.py`

This sets up SQLAlchemy:

- database engine
- session factory
- base model class
- dependency to open/close DB sessions per request

Why needed:
Without this, every route would manually manage DB connections, which is error-prone.

### `backend/app/models/llm_log.py`

This defines the persistent observability record.

Each row represents one LLM interaction and stores:

- prompt
- response
- model name
- latency
- token counts
- feedback
- timestamp

Why needed:
This is the central trace object for your mini observability platform.

### `backend/app/schemas/llm_log.py`

These are Pydantic request/response schemas.

Why needed:

- input validation
- API contracts
- typed responses for frontend integration

### `backend/app/services/groq_client.py`

This is the LLM provider wrapper.

Responsibilities:

- send prompts to Groq
- measure latency
- read provider token usage
- fall back to token estimation

Why needed:
Provider integration should not live inside API routes. Wrapping it keeps the routes clean and makes future provider changes easier.

### `backend/app/services/llm_observer.py`

This is the logging wrapper for LLM calls.

Responsibilities:

- call the provider wrapper
- capture telemetry for observability
- persist the trace row
- return the logged result to the API layer

Why needed:
This makes observability systematic instead of optional. Every LLM call passes through one wrapper that guarantees trace logging.

### `backend/app/services/token_counter.py`

This provides rough token estimation.

Why needed:
Some providers or edge cases may not return exact token counts. In observability systems, approximate usage is still valuable for dashboards, debugging, and cost monitoring.

### `backend/app/services/observability_service.py`

This is the trace persistence layer.

Responsibilities:

- create log rows
- fetch recent logs
- update feedback
- compute summary stats

Why needed:
It keeps data logic out of routes and makes the design more maintainable.

### `backend/app/api/routes.py`

This exposes the backend API:

- `GET /api/health`
- `POST /api/chat`
- `GET /api/logs`
- `POST /api/logs/{id}/feedback`
- `GET /api/stats`

Why needed:
These routes map directly to the UI and the observability workflow.

## 5. Frontend File-by-File Explanation

### `frontend/app/page.tsx`

This is the dashboard page.

It loads:

- aggregate stats
- recent LLM logs

### `frontend/app/lib/api.ts`

This file centralizes backend API calls.

Why needed:
It avoids duplicating fetch logic throughout the UI.

### `frontend/app/lib/types.ts`

Shared frontend types for logs and stats.

Why needed:
Typed contracts reduce mistakes and make the dashboard easier to maintain.

### `frontend/app/components/StatsCards.tsx`

Displays top-level observability KPIs:

- total requests
- average latency
- token usage
- feedback totals

### `frontend/app/components/LogsTable.tsx`

Displays each trace row:

- prompt
- response
- model
- latency
- tokens
- feedback controls

### `frontend/app/components/FeedbackButtons.tsx`

Lets the user add thumbs up/down feedback.

Why needed:
Feedback is a key observability signal. In real systems it helps evaluate quality, UX, and model alignment.

### `frontend/app/globals.css`

All global styling for the dashboard.

Why needed:
A visually clean dashboard makes the project feel more product-like in interviews.

## 6. Database Schema

### `llm_logs`

| Column | Purpose |
|---|---|
| `id` | Unique trace id |
| `prompt` | Original user input |
| `response` | Model output |
| `model_name` | Which model handled the request |
| `latency_ms` | Time taken by the provider call |
| `prompt_tokens` | Input token usage |
| `completion_tokens` | Output token usage |
| `total_tokens` | Total usage |
| `feedback` | `up` or `down` |
| `created_at` | Timestamp for timeline analysis |

## 7. How to Run Locally

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`.

## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

On Windows PowerShell:

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Frontend runs on `http://localhost:3000`.

## 8. Example API Usage

Use this to create a logged LLM request:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain retrieval augmented generation in 3 bullets"}'
```

View logs:

```bash
curl http://localhost:8000/api/logs
```

Submit feedback:

```bash
curl -X POST http://localhost:8000/api/logs/1/feedback \
  -H "Content-Type: application/json" \
  -d '{"feedback":"up"}'
```

## 9. How to Explain This in an Interview

A strong answer is:

> I built a lightweight observability platform for LLM applications. Every inference request is wrapped in a provider client that captures prompt, response, latency, model name, and token usage. That telemetry is persisted in a relational database and exposed through a dashboard for trace inspection and user feedback. I separated provider integration, persistence, schemas, and routes so the system stays easy to test and extend.

## 10. Common Design Decisions and Why

### Why FastAPI?

- fast to build
- typed APIs
- excellent for async HTTP calls to LLM providers

### Why SQLite first?

- zero setup for interviews
- still demonstrates schema design and persistence
- can switch to PostgreSQL via `DATABASE_URL`

### Why a service layer?

- cleaner routes
- easier provider swapping
- easier testing
- clearer architecture story

### Why store prompt and response?

Because observability is not only system metrics. You also need semantic traces to debug prompt quality, hallucinations, response failures, and user dissatisfaction.

### Why track latency and token usage?

- latency helps with performance monitoring and SLOs
- tokens help with usage monitoring and cost visibility

## 11. How to Extend This

### Add RAG

- add document ingestion pipeline
- add embeddings + vector database
- log retrieval context alongside prompt/response
- store cited chunks for debugging

### Add analytics

- latency percentiles
- token cost per day
- model comparison charts
- feedback trends over time

### Add scaling

- move from SQLite to PostgreSQL
- add Redis caching
- add background workers for analytics aggregation
- add pagination and filtering
- add auth and multi-tenant project separation

## 12. Interview Questions You Should Expect

### 1. Why did you separate `GroqClient` from the API routes?

How to answer:

Because provider logic changes more often than API contracts. Keeping it in a service isolates vendor-specific code, makes testing easier, and lets me swap Groq for OpenAI, Anthropic, or Azure with minimal route changes.

### 2. How do you measure latency?

How to answer:

I start a timer immediately before the outbound provider request and stop it immediately after the response returns. That gives provider-call latency, which is a key observability signal for model responsiveness.

### 3. What if the provider does not return token counts?

How to answer:

I fall back to local estimation. It is not exact, but it preserves the observability signal so I can still reason about usage and cost trends.

### 4. Why store feedback?

How to answer:

Raw traces tell me what happened technically, but feedback tells me whether the answer was useful. Combining both helps debug model quality and user satisfaction.

### 5. How would you make this production-ready?

How to answer:

- add auth and RBAC
- use PostgreSQL
- add background jobs
- add retries and circuit breaking for provider failures
- add trace filtering, pagination, and analytics
- add structured logging and metrics export

### 6. How is this similar to Langfuse?

How to answer:

It follows the same core idea: capture LLM traces, enrich them with metadata, persist them, and make them inspectable. The difference is that this version is intentionally simplified for an interview.

## 13. What to Say About Observability

If the interviewer asks what observability means in LLM systems, say:

> Observability for LLM applications means capturing enough runtime context to understand not just infrastructure health, but model behavior. That includes prompts, outputs, latency, token usage, quality signals like feedback, and eventually retrieval context, costs, and failure patterns.

## 14. Next Best Improvements

If you get extra time, add:

1. prompt/response filtering
2. pagination
3. cost estimation per request
4. tags and trace ids
5. session or conversation grouping
6. charts for request volume and latency

## 15. Final Interview Framing

This is a strong interview project because it demonstrates:

- LLM integration
- backend API design
- observability thinking
- product intuition
- full-stack implementation
- extensible architecture

If you want, I can do the next step too: generate a polished `ARCHITECTURE.md`, sample screenshots/mock UI explanation, and a set of mock interview answers you can rehearse aloud.
