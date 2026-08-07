---
name: common-read-hard-drive
description: Read hard drive statistics and disk space metrics for the system.
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
# Read Hard Drive Skill

Use this skill when asked to check hard drive health, disk usage, partition capacity, or storage status.

### Actions & Telemetry
- Check the disk space metrics via `get_system_status`.
- Look for fields like `disk-space` (Linux) or `disk-usage` (Confluence) or attachment partition usage.
- If disk space usage is above 80%, flag it as a warning.
