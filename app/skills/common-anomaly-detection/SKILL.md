---
name: common-anomaly-detection
description: Query metrics from systems and detect threshold breaches (e.g. CPU load
  > 90%, process_down == 0).
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
# Anomaly Detection Skill

Use this skill when tasked with identifying active performance anomalies or system outages.

### Threshold Rules & Outage Criteria
1. **Linux Systems**:
   - Outage: `node-exporter-status` == 0 (implies `node_exporter` is down). Alert severity is CRITICAL.
   - Resource Alert: `cpu-load` > 90.0% or `ram-usage` > 90.0% or `disk-space` > 80.0%. Alert severity is WARNING.
2. **Jira Servers**:
   - JVM Memory Exhaustion: `jvm-heap` > 95%. Alert severity is CRITICAL.
   - Response Latency: `db-connect-time` > 2000.0 ms. Alert severity is WARNING.
3. **Confluence Servers**:
   - Synchronizer drop: `ws-status` == 0 (implies collaborative editor ws down). Alert severity is CRITICAL.
   - Disk space: `disk-usage` >= 80.0% (labeled '/dev/hd1'). Alert severity is WARNING.

### Guidelines
- First, call `list_systems` to discover what servers are running.
- For each system, call `get_system_status(system_id)` to review current metrics.
- Compare metrics against the criteria above.
- If any threshold is breached, flag it to the orchestrator as an active alert, showing the value and severity.
- Suggest remediation options based on system instructions.
