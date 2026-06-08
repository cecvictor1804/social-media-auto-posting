"""Google Gemini drafting provider.

Uses the google-genai SDK with a JSON response mime type + schema. The SDK call
is synchronous, so it's run in a thread to keep the async interface uniform.
"""

from __future__ import annotations

import asyncio
import json

from app.ai.base import DraftError, DraftRequest, build_prompt, response_schema
from app.config import settings
from app.models import AIProvider


class GeminiProvider:
    provider = AIProvider.gemini

    async def draft(self, request: DraftRequest) -> dict[str, str]:
        return await asyncio.to_thread(self._draft_sync, request)

    def _draft_sync(self, request: DraftRequest) -> dict[str, str]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        try:
            resp = client.models.generate_content(
                model=request.model,
                contents=build_prompt(request),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema(request),
                ),
            )
        except Exception as exc:
            raise DraftError(f"Gemini drafting failed: {exc}") from exc

        text = resp.text
        if not text:
            raise DraftError("Gemini returned no text")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise DraftError(f"Gemini returned invalid JSON: {exc}") from exc
