"""Minimal fake SDK response objects, shaped like the real
`openai.types.chat.ChatCompletion` / `azure.ai.inference.models.ChatCompletions`
objects `inference_client.py` reads attributes off of. Both backends
expose the same attribute names for the parts we use
(`.choices[0].message.content`, `.choices[0].delta.content`,
`.usage.prompt_tokens`, ...), so one set of fakes covers both.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Optional


class FakeUsage:
    def __init__(
        self,
        *,
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        total_tokens: Optional[int] = None,
        cached_tokens: Optional[int] = None,
        reasoning_tokens: Optional[int] = None,
    ) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = (
            total_tokens
            if total_tokens is not None
            else (
                (prompt_tokens or 0) + (completion_tokens or 0)
                if prompt_tokens is not None and completion_tokens is not None
                else None
            )
        )
        self.prompt_tokens_details = SimpleNamespace(cached_tokens=cached_tokens) if cached_tokens is not None else None
        self.completion_tokens_details = (
            SimpleNamespace(reasoning_tokens=reasoning_tokens) if reasoning_tokens is not None else None
        )


class FakeMessage:
    def __init__(self, content: Optional[str]) -> None:
        self.content = content


class FakeChoice:
    def __init__(self, content: Optional[str], finish_reason: Optional[str] = "stop") -> None:
        self.message = FakeMessage(content)
        self.finish_reason = finish_reason


class FakeCompletionResponse:
    """A non-streaming response."""

    def __init__(self, *, id: str = "req-0001", content: Optional[str], usage: Optional[FakeUsage], finish_reason: str = "stop") -> None:
        self.id = id
        self.choices = [FakeChoice(content, finish_reason)]
        self.usage = usage


class FakeDelta:
    def __init__(self, content: Optional[str] = None) -> None:
        self.content = content


class FakeStreamChoice:
    def __init__(self, content: Optional[str] = None, finish_reason: Optional[str] = None) -> None:
        self.delta = FakeDelta(content)
        self.finish_reason = finish_reason


class FakeStreamChunk:
    """One streamed chunk. A chunk with no content and no finish_reason
    and no usage has an empty `choices` list, matching a real
    usage-only trailing chunk.
    """

    def __init__(
        self,
        *,
        id: str = "req-0001",
        content: Optional[str] = None,
        finish_reason: Optional[str] = None,
        usage: Optional[FakeUsage] = None,
    ) -> None:
        self.id = id
        self.choices = [FakeStreamChoice(content, finish_reason)] if content is not None or finish_reason else []
        self.usage = usage


def make_openai_status_error(status_code: int, message: str = "error"):
    import httpx
    import openai

    response = httpx.Response(status_code, request=httpx.Request("POST", "https://example.test"))
    return openai.APIStatusError(message, response=response, body=None)


def make_http_response_error(status_code: int, message: str = "error"):
    from azure.core.exceptions import HttpResponseError
    from azure.core.pipeline.transport import HttpResponse

    class _FakeResponse:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code
            self.reason = "error"
            self.headers = {}
            self.content_type = None

        def text(self) -> str:
            return ""

        def body(self):
            return None

    return HttpResponseError(message=message, response=_FakeResponse(status_code))
