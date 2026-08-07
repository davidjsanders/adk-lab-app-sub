---
name: jira-restarting
description: Restart Atlassian Jira application services.
agent_types:
- Jira
categories:
- SaaS
- on-prem
license: Apache 2.0
---
# Restarting Jira Skill

Use this skill when Jira needs to be restarted due to JVM leaks, connection exhaustion, or high latency.

### Guidelines
- Restarting Jira causes temporary downtime.
- ALWAYS warn the user before calling `RESTART_JIRA`.
- Execute `RESTART_JIRA` command via `execute_system_command` on `jira-app-01`.
