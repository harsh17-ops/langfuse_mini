from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import requests


@dataclass
class ObservedSpan:
    name: str
    span_type: str
    start_time: float


class MiniLangfuseSDK:
    """
    Small instrumentation helper for interviews.

    In a real SDK this would stream traces asynchronously and support nested
    context propagation. For this project it demonstrates the contract between
    an application and the observability backend.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def log_generation(
        self,
        *,
        prompt: str,
        model_name: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        prompt_template_name: str | None = None,
        prompt_template_version: int | None = None,
    ) -> dict:
        payload = {
            "name": "sdk-generation",
            "input": prompt,
            "model_name": model_name,
            "session_id": session_id,
            "user_id": user_id,
            "prompt_template_name": prompt_template_name,
            "prompt_template_version": prompt_template_version,
        }
        response = requests.post(f"{self.base_url}/api/traces/generate", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()

    @contextmanager
    def observe_span(self, name: str, span_type: str = "custom") -> Iterator[ObservedSpan]:
        span = ObservedSpan(name=name, span_type=span_type, start_time=time.perf_counter())
        try:
            yield span
        finally:
            _ = (time.perf_counter() - span.start_time) * 1000
