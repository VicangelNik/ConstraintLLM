from __future__ import annotations

import time

from openai import APITimeoutError, APIConnectionError, InternalServerError, OpenAI

from .config import Settings, get_settings


class OpenAICompatibleLLM:
    """Wrapper around an OpenAI-compatible chat completion API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.api_base,
            timeout=settings.request_timeout,
        )

    def __call__(self, system_prompt: str, prompt: str, temperature: float = 0.01) -> str:
        last_error: Exception | None = None
        for attempt in range(self.settings.request_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.settings.model_name,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                )
                message = response.choices[0].message
                return (message.content or "").strip()
            except (APITimeoutError, APIConnectionError, InternalServerError) as exc:
                last_error = exc
                if attempt >= self.settings.request_retries:
                    break
                time.sleep(max(1, self.settings.request_retry_backoff) * (attempt + 1))
        if last_error is not None:
            raise last_error
        return ""


def get_llm(settings: Settings | None = None) -> OpenAICompatibleLLM:
    """Return the default model caller."""
    return OpenAICompatibleLLM(settings or get_settings())
