---
name: common-baseline-learning
description: Evaluate metrics relative to historical or standard baseline ranges (e.g.
  Jira normal active DB connection count is 5-20).
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
# Baseline Learning Skill

Use this skill to determine if a system is operating within its normal bounds or exhibits anomalous activity relative to typical baselines.

### Normal Operating Baselines
1. **Linux Servers**:
   - CPU Load: 10% - 40%
   - RAM Usage: 30% - 60%
   - Disk space growth: < 0.1% per hour
2. **Jira App Servers**:
   - JVM Heap space: 800MB - 3000MB
   - DB Connection Pool leases: 4 - 25
   - HTTP Latency: 60ms - 300ms
   - HTTP 5xx Error rate: < 1.0%
3. **Confluence Servers**:
   - Websocket: Always CONNECTED (1)
   - Attachment disk: 30% - 70%

### Guidelines
- Compare the returned values from `get_system_status` with these typical values.
- If a system has a metric outside this range (e.g., Jira DB leases at 40 even if the pool max is 50), report that the metric is elevated and represents a baseline deviation.
- Flag baseline deviations to help catch issues before they trigger hard threshold alarms.
