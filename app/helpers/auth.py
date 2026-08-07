import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import httpx
from urllib.parse import urlparse


class GoogleCloudRunAuth(httpx.Auth):
    """Auth class for fetching Google ID tokens for Cloud Run audiences."""
    def __init__(self, audience: str):
        self.audience = audience
        self._auth_req = Request()

    def auth_flow(self, request: httpx.Request):
        # Dynamically fetch ID token for Cloud Run target
        token = id_token.fetch_id_token(self._auth_req, self.audience)
        request.headers["Authorization"] = f"Bearer {token}"
        yield request


def get_authenticated_client(service_url: str, timeout: httpx.Timeout | None = None) -> httpx.AsyncClient:
    """Returns an httpx.AsyncClient pre-configured with Google ID token auth for Cloud Run."""
    parsed = urlparse(service_url)
    audience = f"{parsed.scheme}://{parsed.hostname}"
    resolved_timeout = timeout or httpx.Timeout(120.0)

    if "127.0.0.1" in audience or "localhost" in audience:
        return httpx.AsyncClient(timeout=resolved_timeout)
    return httpx.AsyncClient(
        auth=GoogleCloudRunAuth(audience),
        timeout=resolved_timeout
    )
