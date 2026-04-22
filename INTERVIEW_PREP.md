# Interview Prep

## 60-Second Project Summary

I built a mini Langfuse-style observability platform for LLM applications using FastAPI, Next.js, SQLite, and the Groq API. Every model call is wrapped so I can capture prompt, response, latency, model name, token usage, and user feedback. The backend persists those traces, and the frontend dashboard lets me inspect them and reason about model behavior and quality.

## Strong Answers

### What problem does this solve?

It makes LLM behavior inspectable. Without trace logging, model failures are hard to debug because you do not know what prompt was sent, how long it took, how many tokens it used, or whether the response was useful.

### Why is token tracking important?

Token usage is a proxy for cost and efficiency. It helps answer whether the app is becoming more expensive over time and whether prompt design is wasteful.

### Why collect thumbs up/down?

Because system metrics alone do not tell me if the answer was good. Feedback gives me a quality signal that I can correlate with prompts, models, and latency.

### What tradeoff did you make for interview speed?

I used SQLite and synchronous persistence because they reduce setup complexity. I kept the architecture production-oriented so swapping in PostgreSQL, migrations, caching, and analytics later is straightforward.

## Follow-Up Questions to Practice

1. How would you trace multi-turn conversations?
2. How would you compare multiple models on the same prompts?
3. How would you estimate cost per request?
4. How would you add RAG observability?
5. How would you prevent sensitive prompt data from being exposed?

