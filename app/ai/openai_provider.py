"""OpenAI drafting provider.

Uses Chat Completions with a JSON-schema response format so the model returns
one draft per platform as strict JSON.
"""

from __future__ import annotations

import json

from app.ai.base import DraftError, DraftRequest, build_prompt, response_schema
from app.config import settings
from app.models import AIProvider


class OpenAIProvider:
    provider = AIProvider.openai

    async def draft(self, request: DraftRequest) -> dict[str, str]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        try:
            resp = await client.chat.completions.create(
                model=request.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You return only the requested JSON object.",
                    },
                    {"role": "user", "content": build_prompt(request)},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "platform_drafts",
                        "strict": True,
                        "schema": response_schema(request),
                    },
                },
            )
        except Exception as exc:
            raise DraftError(f"OpenAI drafting failed: {exc}") from exc

        content = resp.choices[0].message.content
        if not content:
            raise DraftError("OpenAI returned no content")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise DraftError(f"OpenAI returned invalid JSON: {exc}") from exc
