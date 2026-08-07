---
name: confluence-ops
description: Operator rules for Atlassian Confluence server, including attachments
  storage purges, collaborative websockets reconnects, and system restarts.
license: Apache 2.0
---
# Atlassian Confluence Server Operations

Use this skill when interacting with Atlassian Confluence applications (`confluence-app-01`).

### Actions Available
- **`RECONNECT_WEBSOCKETS`**: Re-establish websocket synchronization for collaborative editing session editor. Use when websocket state drops to offline (0).
- **`PURGE_ATTACHMENTS`**: Purge old logs and cache to free up attachment storage space. Use when disk usage percent is elevated or critical.
- **`REBOOT`**: Restart the Confluence application server. Use as a last-resort recovery mechanism.
- **`RESET_SIMULATION`**: Revert Confluence emulator settings to default.

### Guidelines
- Always render the system card using `render_system_card("confluence-app-01")` before and after running any command.
- If collaborative editing drops, try to call `RECONNECT_WEBSOCKETS` first before attempting a full system restart.
