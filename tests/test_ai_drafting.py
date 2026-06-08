import pytest

import app.ai.base as aibase
import app.ai.drafting as drafting
from app.ai import DraftError, DraftRequest, available_models
from app.models import AIProvider, Platform
from app.publishers.base import PLATFORM_CHAR_LIMITS


def test_registry_filters_unconfigured(monkeypatch):
    # Only Anthropic configured.
    monkeypatch.setattr(
        aibase, "provider_configured", lambda p: p is AIProvider.anthropic
    )
    models = available_models()
    assert models, "expected at least one model"
    assert all(m.provider is AIProvider.anthropic for m in models)


async def test_orchestrator_routes_and_trims(monkeypatch):
    # Pretend every provider is configured.
    monkeypatch.setattr(drafting, "provider_configured", lambda p: True)

    class FakeProvider:
        provider = AIProvider.anthropic

        async def draft(self, request):
            return {
                "linkedin": "x" * 5000,  # over LinkedIn's 3000 limit
                "threads": "hello threads",
            }

    monkeypatch.setattr(drafting, "_provider_for", lambda provider: FakeProvider())

    out = await drafting.draft_posts(
        DraftRequest(
            brief="launch",
            platforms=[Platform.linkedin, Platform.threads],
            model="claude-opus-4-8",
        )
    )
    assert len(out[Platform.linkedin]) == PLATFORM_CHAR_LIMITS[Platform.linkedin]
    assert out[Platform.threads] == "hello threads"


async def test_unconfigured_provider_raises(monkeypatch):
    monkeypatch.setattr(drafting, "provider_configured", lambda p: False)
    with pytest.raises(DraftError):
        await drafting.draft_posts(
            DraftRequest(brief="x", platforms=[Platform.threads], model="claude-opus-4-8")
        )
