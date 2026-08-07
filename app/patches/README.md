# Sysman Agent Patches

This directory contains various monkey-patches and subclass overrides designed to work around limitations, bugs, and sync replication delays in the current version of the Agent Development Kit (ADK) SDK (v.2.6.2).

## Available Patches

- **[CredentialManager Patch](file:///usr/local/google/home/djsanders/dev/adk-lab-app/sysman-v2/sysman-agent/app/patches/patch_credential_manager.md):** Solves the missing `function_call_id` pre-authorization crash and implements retry loops to mitigate transient GCP connection/sync delays.
- **[Finalize Credentials Patch](file:///usr/local/google/home/djsanders/dev/adk-lab-app/sysman-v2/sysman-agent/app/patches/patch_finalize_credentials.md):** Intercepts authentication finalization failures caused by mismatched User IDs during Agent2Agent (A2A) orchestration.
- **[GCP Skill Registry Override](file:///usr/local/google/home/djsanders/dev/adk-lab-app/sysman-v2/sysman-agent/app/patches/patched_gcp_skill_registry.md):** Overrides `GCPSkillRegistry` client settings to follow HTTP redirects (HTTP 302/307) during skill downloads and gracefully handles invalid skill registry schemas without aborting the entire search process.

## Activation

Monkey-patches are automatically applied at runtime during application initialization in the agent entrypoint: [app/agent.py](file:///usr/local/google/home/djsanders/dev/adk-lab-app/sysman-v2/sysman-agent/app/agent.py).
