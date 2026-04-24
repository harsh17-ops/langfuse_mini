try:
    import tiktoken
except ImportError:  # pragma: no cover - optional dependency in lightweight environments
    tiktoken = None


def count_tokens(text: str) -> int:
    """
    Prefer deterministic token counting when the tokenizer library is available.

    LLM observability depends on usage visibility. If exact provider numbers are missing,
    we still want repeatable local counting for token and cost estimates.
    """
    if tiktoken is not None:
        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    return estimate_tokens(text)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.split()) + len(text) // 4)


MODEL_PRICING_PER_1K = {
    "llama-3.1-8b-instant": 0.05,
    "llama-3.1-70b-versatile": 0.79,
}


def estimate_cost_usd(model_name: str, total_tokens: int) -> float:
    price_per_1k = MODEL_PRICING_PER_1K.get(model_name, 0.05)
    return round((total_tokens / 1000) * price_per_1k, 6)
