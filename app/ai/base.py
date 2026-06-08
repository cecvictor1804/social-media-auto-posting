"""AI drafting types, model registry, and the shared prompt/schema builder.

The compose UI offers a per-draft model dropdown built from ``available_models``
(only providers whose API key is configured are listed). The orchestrator maps a
chosen model id back to its provider via the registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.config import settings
from app.models import AIProvider, Platform
from app.publishers.base import PLATFORM_CHAR_LIMITS


@dataclass(frozen=True, slots=True)
class ModelInfo:
    id: str
    label: str
    provider: AIProvider


# Selectable models per provider. Claude Opus 4.8 is the recommended default.
MODEL_REGISTRY: tuple[ModelInfo, ...] = (
    ModelInfo("claude-opus-4-8", "Claude Opus 4.8", AIProvider.anthropic),
    ModelInfo("claude-sonnet-4-6", "Claude Sonnet 4.6", AIProvider.anthropic),
    ModelInfo("claude-haiku-4-5", "Claude Haiku 4.5", AIProvider.anthropic),
    ModelInfo("gpt-4o", "OpenAI GPT-4o", AIProvider.openai),
    ModelInfo("gpt-4o-mini", "OpenAI GPT-4o mini", AIProvider.openai),
    ModelInfo("gemini-2.0-flash", "Gemini 2.0 Flash", AIProvider.gemini),
    ModelInfo("gemini-1.5-pro", "Gemini 1.5 Pro", AIProvider.gemini),
)


@dataclass(slots=True)
class DraftRequest:
    brief: str
    platforms: list[Platform]
    tone: str = "professional"
    model: str = field(default_factory=lambda: settings.default_ai_model)


class DraftError(Exception):
    pass


def provider_configured(provider: AIProvider) -> bool:
    return {
        AIProvider.anthropic: bool(settings.anthropic_api_key),
        AIProvider.openai: bool(settings.openai_api_key),
        AIProvider.gemini: bool(settings.gemini_api_key),
    }[provider]


def available_models() -> list[ModelInfo]:
    """Models whose provider has a configured API key."""
    return [m for m in MODEL_REGISTRY if provider_configured(m.provider)]


def model_info(model_id: str) -> ModelInfo:
    for m in MODEL_REGISTRY:
        if m.id == model_id:
            return m
    raise DraftError(f"Unknown model id: {model_id!r}")


def build_prompt(request: DraftRequest) -> str:
    """Shared natural-language instruction used across all providers."""
    lines = [
        "You are a social media copywriter. Draft one post per requested platform "
        "from the brief below.",
        "",
        f"Brief: {request.brief}",
        f"Tone: {request.tone}",
        "",
        "Requirements:",
        "- Tailor each post to its platform's conventions and audience.",
        "- Respect each platform's maximum character length (hard limit).",
        "- Return ONLY a JSON object keyed by platform name; no extra commentary.",
        "",
        "Platforms and limits:",
    ]
    for p in request.platforms:
        lines.append(f"- {p.value}: max {PLATFORM_CHAR_LIMITS[p]} characters")
    return "\n".join(lines)


def response_schema(request: DraftRequest) -> dict:
    """JSON schema with one required string property per requested platform."""
    props = {p.value: {"type": "string"} for p in request.platforms}
    return {
        "type": "object",
        "properties": props,
        "required": [p.value for p in request.platforms],
        "additionalProperties": False,
    }
