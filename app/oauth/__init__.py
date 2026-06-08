"""OAuth connect + token-refresh flows for each platform."""

from app.models import Platform
from app.oauth.base import ConnectedAccount, OAuthProvider, OAuthError

__all__ = ["get_oauth_provider", "ConnectedAccount", "OAuthProvider", "OAuthError"]


def get_oauth_provider(platform: Platform) -> OAuthProvider:
    from app.oauth.facebook import FacebookOAuth
    from app.oauth.linkedin import LinkedInOAuth
    from app.oauth.threads import ThreadsOAuth

    mapping: dict[Platform, type[OAuthProvider]] = {
        Platform.facebook: FacebookOAuth,
        Platform.linkedin: LinkedInOAuth,
        Platform.threads: ThreadsOAuth,
    }
    return mapping[platform]()
