import json
from collections import Counter

from app.services.evaluation_service import EvaluationService


DEFAULT_KNOWLEDGE_BASE = [
    "Retrieval-Augmented Generation combines retrieval with generation so the answer can use external context instead of relying only on parametric memory.",
    "Transformers use self-attention to let every token attend to every other token and capture long-range dependencies.",
    "Prompt versioning is useful because prompt wording affects quality, latency, token usage, and evaluation outcomes.",
    "LLM observability should track prompts, outputs, latency, token usage, feedback, and evaluation signals together.",
    "Encoder-only models are usually strong for understanding tasks, while decoder-only models are strong for generation tasks.",
]


class RetrievalService:
    def __init__(self) -> None:
        self.evaluation_service = EvaluationService()

    def retrieve(self, query: str, knowledge_base: list[str] | None = None, top_k: int = 3) -> list[dict]:
        corpus = knowledge_base or DEFAULT_KNOWLEDGE_BASE
        query_terms = Counter(query.lower().split())
        scored_chunks: list[dict] = []

        for chunk in corpus:
            chunk_terms = Counter(chunk.lower().split())
            lexical_overlap = sum((query_terms & chunk_terms).values())
            semantic_score = self.evaluation_service.score_semantic_similarity(query, chunk)
            blended_score = round((lexical_overlap * 0.15) + semantic_score, 4)
            scored_chunks.append(
                {
                    "content": chunk,
                    "lexical_overlap": lexical_overlap,
                    "semantic_score": semantic_score,
                    "score": blended_score,
                }
            )

        scored_chunks.sort(key=lambda item: item["score"], reverse=True)
        return scored_chunks[:top_k]

    def build_retrieval_metadata(self, chunks: list[dict]) -> str:
        return json.dumps({"retrieved_chunks": chunks}, ensure_ascii=True)

    def build_augmented_prompt(self, query: str, chunks: list[dict]) -> str:
        context = "\n\n".join([f"Context {index + 1}: {chunk['content']}" for index, chunk in enumerate(chunks)])
        return f"Use the following retrieved context when helpful.\n\n{context}\n\nUser request: {query}"

    def grounded_overlap(self, response: str, chunks: list[dict]) -> float:
        if not chunks:
            return 0.0
        combined_context = " ".join(chunk["content"] for chunk in chunks)
        return self.evaluation_service.score_semantic_similarity(combined_context, response)
