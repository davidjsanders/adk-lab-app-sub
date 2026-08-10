import os
import logging
from urllib.parse import urlparse
from typing import Optional, Tuple
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, HttpAuth, HttpCredentials
from google.adk.tools.openapi_tool.auth.auth_helpers import service_account_scheme_credential
from google.adk.auth.auth_credential import ServiceAccount
from fastapi.openapi.models import HTTPBearer
from google.adk.auth.auth_schemes import AuthScheme

logger = logging.getLogger(__name__)


def is_google_api(url: str) -> bool:
    """Checks if the given URL points to a Google API endpoint."""
    parsed_url = urlparse(url)
    if not parsed_url.hostname:
        return False
    return (
        parsed_url.hostname == "googleapis.com"
        or parsed_url.hostname.endswith(".googleapis.com")
    )


def generate_impersonated_id_token(impersonate_sa: str, audience: str) -> str:
    """Generates an impersonated OIDC ID token for the given service account and audience."""
    import google.auth
    from google.auth.transport.requests import Request
    import requests

    parsed_url = urlparse(audience)
    if parsed_url.scheme and parsed_url.netloc:
        target_audience = f"{parsed_url.scheme}://{parsed_url.netloc}"
    else:
        target_audience = audience

    credentials, _ = google.auth.default()
    auth_request = Request()
    credentials.refresh(auth_request)

    url = f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{impersonate_sa}:generateIdToken"
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    body = {
        "audience": target_audience,
        "includeEmail": True,
    }
    response = requests.post(url, json=body, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()["token"]


def get_mcp_auth(endpoint_uri: str) -> Tuple[Optional[AuthScheme], Optional[AuthCredential]]:
    """Resolves dynamic auth scheme and credentials for the given MCP endpoint URL.
    
    If IMPERSONATE_SA is set in environment, generates an impersonated OIDC ID token.
    Otherwise, returns standard ADK ServiceAccount credentials config.
    """
    if not endpoint_uri or is_google_api(endpoint_uri):
        return None, None

    parsed = urlparse(endpoint_uri)
    audience = f"{parsed.scheme}://{parsed.netloc}"

    impersonate_sa = os.environ.get("IMPERSONATE_SA")
    if impersonate_sa:
        logger.info("Generating impersonated ID token for SA %s and audience %s", impersonate_sa, audience)
        id_token = generate_impersonated_id_token(impersonate_sa, audience)
        
        auth_scheme = HTTPBearer(bearerFormat="JWT")
        auth_credential = AuthCredential(
            auth_type=AuthCredentialTypes.HTTP,
            http=HttpAuth(
                scheme="bearer",
                credentials=HttpCredentials(token=id_token)
            )
        )
        return auth_scheme, auth_credential
        
    logger.info("Applying ADK Service Account authentication for audience: %s", audience)
    sa_config = ServiceAccount(
        use_default_credential=True,
        use_id_token=True,
        audience=audience
    )
    return service_account_scheme_credential(sa_config)
