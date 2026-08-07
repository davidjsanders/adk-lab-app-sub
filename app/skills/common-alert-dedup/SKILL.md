---
name: common-alert-dedup
description: Group and deduplicate multiple alerts originating from the same root-cause
  failure (e.g. Jira and Confluence both failing due to DB outage).
agent_types:
- Linux
- Jira
- Confluence
categories:
- Linux
- on-prem
- SaaS
license: Apache 2.0
---
# Alert Deduplication and Correlation Skill

Use this skill to correlate alarms across different hosts.

### Outage Correlation Scenarios
1. **Shared Database Outage**:
   - If both `jira-app-01` (DB connections pool exhausted) and `confluence-app-01` (or another app) report connection errors, database timeouts, or latency spikes in their syslog entries, correlate them.
   - Summarize this as a single "Systemic Database Outage" incident rather than reporting two separate independent outages.
2. **Network/Websocket Interruptions**:
   - If multiple application websocket connections drop simultaneously, flag it as a network/infrastructure event.

### Guidelines
- Analyze status payloads for all systems collectively.
- If multiple systems are UNHEALTHY or DEGRADED, check their recent logs for similar keywords (e.g., "Connection refused", "Timeout", "DB Pool").
- Consolidate related issues into a unified summary report for the orchestrator, pinpointing the likely shared upstream service dependency.
