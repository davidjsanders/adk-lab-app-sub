---
name: common-format-hard-drive
description: Format a hard drive or disk partition.
agent_types:
- Linux
- Jira
- Confluence
categories:
- Linux
- on-prem
license: Apache 2.0
---
# Format Hard Drive Skill

Use this skill when clean partition formats or wiping disks is requested.

### Guidelines
- Formatting a disk partition is destructive.
- ALWAYS ask the user for confirmation before performing formatting actions.
- This action is simulated by rebooting or resetting the system config to defaults (e.g. `RESET_SIMULATION`).
