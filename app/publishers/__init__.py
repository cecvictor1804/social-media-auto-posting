"""Platform publishers."""

from app.models import Platform
from app.publishers.base import (
    PLATFORM_CHAR_LIMITS,
    PLATFORM_MAX_IMAGES,
    MediaItem,
    PublishError,
    PublishRequest,
    PublishResult,
    Publisher,
    validate_media,
)

__all__ = [
    "get_publisher",
    "Publisher",
    "PublishError",
    "PublishRequest",
    "PublishResult",
    "MediaItem",
    "PLATFORM_CHAR_LIMITS",
    "PLATFORM_MAX_IMAGES",
    "validate_media",
]


def get_publisher(platform: Platform) -> Publisher:
    """Return the publisher implementation for a platform."""
    # Imported lazily to keep module import cheap and side-effect-free.
    from app.publishers.facebook import FacebookPublisher
    from app.publishers.linkedin import LinkedInPublisher
    from app.publishers.threads import ThreadsPublisher

    mapping: dict[Platform, type[Publisher]] = {
        Platform.facebook: FacebookPublisher,
        Platform.linkedin: LinkedInPublisher,
        Platform.threads: ThreadsPublisher,
    }
    return mapping[platform]()
