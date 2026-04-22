def estimate_tokens(text: str) -> int:
    """
    Rough token estimation for observability dashboards.

    Exact token accounting depends on the model tokenizer. For an interview mini-project,
    estimating is acceptable and still demonstrates the important observability idea:
    every request should record usage signals for cost and performance analysis.
    """
    if not text:
        return 0
    return max(1, len(text.split()) + len(text) // 4)

