from __future__ import annotations

import os
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
        disable_thinking = os.environ.get("CONSTRAINTLLM_DISABLE_THINKING", "").strip().lower() in {"1", "true", "yes", "on"}
        for attempt in range(self.settings.request_retries + 1):
            request_start = time.perf_counter()
            try:
                request_kwargs = {
                    "model": self.settings.model_name,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                }
                # 对支持 Qwen chat_template 的后端显式关闭 thinking。
                if disable_thinking:
                    request_kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}

                response = self.client.chat.completions.create(
                    **request_kwargs,
                )
                message = response.choices[0].message
                elapsed = time.perf_counter() - request_start
                print(
                    f"[llm] model={self.settings.model_name} attempt={attempt + 1} "
                    f"thinking={'off' if disable_thinking else 'default'} elapsed={elapsed:.2f}s"
                )
                return (message.content or "").strip()
            except (APITimeoutError, APIConnectionError, InternalServerError) as exc:
                elapsed = time.perf_counter() - request_start
                print(
                    f"[llm] model={self.settings.model_name} attempt={attempt + 1} "
                    f"thinking={'off' if disable_thinking else 'default'} failed_after={elapsed:.2f}s error={type(exc).__name__}"
                )
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
