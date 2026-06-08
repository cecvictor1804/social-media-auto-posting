"""Orchestrator: route a chosen model id to its provider and normalize output."""

from __future__ import annotations

from app.ai.base import (
    DraftError,
    DraftRequest,
    model_info,
    provider_configured,
)
from app.models import AIProvider, Platform
from app.publishers.base import PLATFORM_CHAR_LIMITS


def _provider_for(provider: AIProvider):
    if provider is AIProvider.anthropic:
        from app.ai.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if provider is AIProvider.openai:
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider()
    from app.ai.gemini_provider import GeminiProvider

    return GeminiProvider()


async def draft_posts(request: DraftRequest) -> dict[Platform, str]:
    """Generate one draft per requested platform using the selected model.

    Returns a mapping keyed by :class:`Platform`. Raises :class:`DraftError`
    for unknown/unconfigured models, provider failures, or malformed output.
    """
    if not request.platforms:
        raise DraftError("At least one platform is required")

    info = model_info(request.model)
    if not provider_configured(info.provider):
        raise DraftError(
            f"Provider {info.provider.value} is not configured "
            f"(missing API key). Choose a different model."
        )

    provider = _provider_for(info.provider)
    raw = await provider.draft(request)

    result: dict[Platform, str] = {}
    for platform in request.platforms:
        text = (raw.get(platform.value) or "").strip()
        if not text:
            raise DraftError(f"Model returned no draft for {platform.value}")
        limit = PLATFORM_CHAR_LIMITS[platform]
        # Defensive trim: never hand the publisher an over-limit body.
        result[platform] = text[:limit]
    return result
