---
name: common-handling-high-latency-requests
description: Troubleshoot and remediate high latency or response timeouts.
agent_types:
- Jira
- Confluence
categories:
- SaaS
- on-prem
license: Apache 2.0
---
# Handling High Latency Requests Skill

Use this skill when response latency exceeds normal baselines (e.g. > 2000ms) or when DB connection pool exhaustion is suspected.

### Workflows
- If Jira latency is high due to connection exhaustion, execute `EXPAND_DB_POOL` command on `jira-app-01`.
- If Confluence collaborative websockets are dropping, execute `RECONNECT_WEBSOCKETS` command on `confluence-app-01`.
- If latency remains high, analyze the syslog or application logs using `get_system_logs`.
