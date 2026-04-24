# Interview Prep

## 60-second pitch

I reimplemented the Langfuse core architecture rather than cloning the full product. The backend models observability as `trace -> span -> generation`, stores prompt and response metadata, tracks latency, tokens, and cost, and attaches evaluations through a polymorphic scores table. On top of that I added an NLP-focused evaluation layer with semantic similarity, zero-shot classification, and LLM-as-judge scoring, because that is where an NLP / Transformers engineer can add differentiated value.

## Strong answers

### Why not a single logging table?

Because real LLM applications are multi-step systems. A single flat table loses the structure of retrieval, ranking, generation, and evaluation. Hierarchical traces preserve that execution graph.

### Why a unified scores table?

It lets me query human feedback, model-based metrics, and judge scores through one abstraction. That makes analytics and filtering much simpler.

### Why add prompt versioning?

Prompting is part of the application logic. If you cannot tie generations back to prompt versions, you cannot compare prompt changes scientifically.

### Why is the NLP layer relevant?

Observability tells me what happened. NLP evaluations help me estimate whether the response was useful, coherent, grounded, or on-topic without waiting for humans on every trace.

## Questions they may ask

1. Why did you choose `trace -> span -> generation`?
2. What tradeoffs did you make compared with real Langfuse?
3. Why use sentence-transformers here?
4. Why is LLM-as-judge backgrounded?
5. How would you support RAG pipelines next?
6. How would you scale the scores table?

## How to answer the scope question

If they ask why you did not clone the entire repo, say:

I deliberately reimplemented the Langfuse core rather than the full product surface. The real project includes prompt management, experiments, datasets, integrations, and deployment infrastructure. For interview scope, the highest-signal slice is the observability backbone plus one differentiated evaluation layer.

