# Architecture Walkthrough

## Core idea

This project reimplements the Langfuse observability spine:

- capture one user request as a `Trace`
- break internal work into `Span` records
- persist each LLM call as a `Generation`
- attach evaluations as `Score` rows
- version prompts through `PromptTemplate`

## Why `Trace -> Span -> Generation` matters

A flat logging table cannot represent multi-step AI systems well. In real LLM systems, one user request often triggers:

- retrieval
- ranking
- multiple model calls
- tool usage
- evaluation

Hierarchical tracing is the right abstraction because it preserves structure.

## Score model design

The `scores` table is polymorphic:

- `NUMERIC`
- `BOOLEAN`
- `CATEGORICAL`

That lets one table store:

- human feedback
- semantic similarity
- zero-shot classifier outputs
- LLM-as-judge metrics

This is one of the most important system design choices in the project.

## Observability lifecycle

1. Request arrives
2. Trace is created
3. Generation span is created
4. Groq call is executed
5. Latency is measured
6. Tokens are counted
7. Cost is estimated
8. Generation is stored
9. Evaluations run
10. Scores are written
11. Dashboard reads traces and analytics

## Evaluation lifecycle

### Semantic similarity

Uses `sentence-transformers` when available and a fallback heuristic otherwise.

### Classifier scoring

Uses Hugging Face zero-shot classification when available.

### LLM-as-judge

Runs as a background task so the main response stays fast while deeper evaluation still lands in the score table.

## Prompt management lifecycle

1. Create prompt family
2. Add versions
3. Promote one version to `production`
4. Link generations back to `prompt_template_name` and `prompt_template_version`
5. Compare prompt versions using score and latency analytics

