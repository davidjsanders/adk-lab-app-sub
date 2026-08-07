import os
from dotenv import load_dotenv
from app.classes.settings import Settings

# Populate environment
load_dotenv(override=False)

settings = Settings()

# Apply Service Account Impersonation for local development if IMPERSONATE_SA is set
if settings.impersonate_sa:
    import google.auth
    from google.auth.impersonated_credentials import Credentials
    import logging
    
    logger = logging.getLogger("sysman-agent.config")

    # Only impersonate in local workstation development environments
    if not os.getenv("K_SERVICE") and not os.getenv("APP_URL"):
        original_default = google.auth.default
        cache = []
        def impersonated_default(*args, **kwargs):
            if not cache:
                cache.append(original_default(*args, **kwargs))
            base_creds, project = cache[0]
            impersonated_creds = Credentials(
                source_credentials=base_creds,
                target_principal=settings.impersonate_sa,
                target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            return impersonated_creds, project
        google.auth.default = impersonated_default

        # Patch Credentials to return OIDC ID Tokens instead of Access Tokens when calling Cloud Run
        original_before_request = Credentials.before_request

        def patched_before_request(self, request, method, url, headers):
            if ".run.app" in url:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                audience = f"{parsed.scheme}://{parsed.netloc}"
                
                logger.info("Intercepted Cloud Run request. Generating impersonated OIDC ID token for audience: %s", audience)
                
                from google.auth.impersonated_credentials import IDTokenCredentials
                id_creds = IDTokenCredentials(
                    target_credentials=self,
                    target_audience=audience,
                    include_email=True
                )
                id_creds.refresh(request)
                id_creds.apply(headers)
                return

            return original_before_request(self, request, method, url, headers)

        Credentials.before_request = patched_before_request


