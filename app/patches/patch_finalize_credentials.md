# Patch: A2A Finalize Credentials User ID Alignment Interceptor

## What it does
This patch monkey-patches `google.cloud.iamconnectorcredentials_v1alpha.IAMConnectorCredentialsServiceClient.finalize_credentials` to intercept execution errors during token/credential finalization. Specifically, it catches errors indicating that the state user ID does not match and logs detailed debug instructions.

## Why it's needed
- **A2A Mismatches:** During Agent2Agent (A2A) interactions or nested sub-agent queries, the sub-agents and the caller agent must align their active user identities. If a mismatch is detected, GCP IAM finalization fails with a cryptic message. Intercepting this error allows logging a clear error advising developers to register or update the `request_converter` to align user IDs.

## Where it's used
- Initialized in [app/agent.py](file:///usr/local/google/home/djsanders/dev/adk-lab-app/sysman-v2/sysman-agent/app/agent.py) via `patch_finalize_credentials()`.
