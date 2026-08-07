# Patch: PatchedGCPSkillRegistry for Redirects and Validation Errors

## What it does
This patch provides `PatchedGCPSkillRegistry` (a subclass of `google.adk.integrations.skill_registry.gcp_skill_registry.GCPSkillRegistry`) that overrides:
1. `_create_httpx_client` to set `follow_redirects=True`.
2. `search_skills` to catch, log, and skip individual skills that fail Pydantic validation (e.g. invalid format or metadata field issues), rather than failing the entire search request.

## Why it's needed
- **HTTP 302 Redirect Failure:** The ADK's default client does not follow redirects. If the Skill Registry redirects the client to a Signed URL (e.g. Google Cloud Storage bucket) to download the skill payload, the call fails.
- **Validation Resilience:** In shared environments, some registered skills might contain outdated frontmatter schemas (such as descriptions exceeding characters limits or invalid namespace conventions). The default ADK behavior crashes the entire search query if any single skill is malformed. This subclass gracefully skips malformed skills and returns all valid entries.

## Where it's used
- Used in [app/classes/specialist_agent.py](file:///usr/local/google/home/djsanders/dev/adk-lab-app/sysman-v2/sysman-agent/app/classes/specialist_agent.py) to construct the skill registry.
- Used in [app/classes/registry_helper.py](file:///usr/local/google/home/djsanders/dev/adk-lab-app/sysman-v2/sysman-agent/app/classes/registry_helper.py) when building and listing registered skills.
