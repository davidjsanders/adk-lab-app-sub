# Patch: CredentialManager Sync and Function Call ID Fix

## What it does
This patch monkey-patches `google.adk.auth.credential_manager.CredentialManager.get_auth_credential` to:
1. Ensure `context.function_call_id` is set to `_adk_toolset_auth_AgentRegistrySingleMcpToolset` if it is `None`.
2. Add a retry loop (up to 3 attempts, waiting 2 seconds between attempts) when the credential retrieval fails with a `"Failed to retrieve consent based credential"` error.

## Why it's needed
- **Function Call ID Bug:** In some execution contexts (e.g. initial authorization flow on start), the ADK framework fails to propagate the `function_call_id` into the toolset context. Without this ID, the callback mechanism fails to map the request, crashing the credential collection process.
- **GCP Sync Delay:** When executing tools or fetching credentials immediately after session start/user authorization, the GCP connectors/identity manager may experience transient authorization replication delays. A simple retry mechanism prevents immediate failure and allows synchronization to complete.

## Where it's used
- Initialized in [app/agent.py](file:///usr/local/google/home/djsanders/dev/adk-lab-app/sysman-v2/sysman-agent/app/agent.py) via `patch_credential_manager()`.
