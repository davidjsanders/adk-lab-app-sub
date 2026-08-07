---
name: jira-ops
description: Operator rules for Atlassian Jira server, including DB pool scaling,
  Garbage Collection triggers, and JVM restarts.
license: Apache 2.0
---
# Atlassian Jira Server Operations

Use this skill when interacting with Atlassian Jira applications (`jira-app-01`).

### Actions Available
- **`GC_CLEANUP`**: Force JVM Garbage Collection. Use this as a first-line tactical response for memory creep or high memory warnings.
- **`EXPAND_DB_POOL`**: Expand connection pool capacity (e.g. up to 100 connections). Use when DB connection leases are exhausted.
- **`RESTART_JIRA`**: Reboot the Jira server process. Use as a last-resort remediation for OutOfMemory (OOM) failures or persistent high response latency.
- **`RESET_SIMULATION`**: Revert Jira emulator settings to default.

### Guidelines
- Always render the system card using `render_system_card("jira-app-01")` before and after running any command.
- Warn the user before calling `RESTART_JIRA` as this will temporarily take Jira offline.
