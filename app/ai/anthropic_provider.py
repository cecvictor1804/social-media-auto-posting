"""Anthropic (Claude) drafting provider.

Uses the Messages API with adaptive thinking and structured outputs
(``output_config.format``) so the model returns one draft per platform as
strict JSON. Default model is ``claude-opus-4-8``.
"""

from __future__ import annotations

import json

from app.ai.base import DraftError, DraftRequest, build_prompt, response_schema
from app.config import settings
from app.models import AIProvider


class AnthropicProvider:
    provider = AIProvider.anthropic

    async def draft(self, request: DraftRequest) -> dict[str, str]:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        try:
            resp = await client.messages.create(
                model=request.model,
                max_tokens=4096,
                thinking={"type": "adaptive"},
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": response_schema(request),
                    }
                },
                messages=[{"role": "user", "content": build_prompt(request)}],
            )
        except Exception as exc:  # surface provider errors uniformly
            raise DraftError(f"Anthropic drafting failed: {exc}") from exc

        text = next((b.text for b in resp.content if b.type == "text"), None)
        if not text:
            raise DraftError("Anthropic returned no text content")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise DraftError(f"Anthropic returned invalid JSON: {exc}") from exc
