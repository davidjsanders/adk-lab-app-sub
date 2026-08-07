---
name: common-drift-detection
description: Scan syslog and metrics history to detect slow, gradual trends over time
  (such as JVM memory leaks or disk space fill).
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
# Drift Detection Skill

Use this skill to spot gradual metrics trends that worsen over time, such as slow disk filling or JVM memory leaks (typical in ClassLoader resource leaks).

### Drift Patterns
1. **JVM Memory Leak (Jira/Confluence)**:
   - Check the logs using `get_system_logs(system_id)`. Look for frequent GC warnings or "GC overhead limit exceeded".
   - Review JVM heap telemetry over multiple queries. If JVM memory is steadily climbing and does not decrease after Garbage Collection (`GC_CLEANUP`), identify a "Java Memory Leak (Drift)" issue.
2. **Disk Capacity Growth (Confluence/Linux)**:
   - Inspect attachment directory growth rate. If disk space is climbing by several percent every few minutes (in our mock), identify a "Disk Fill Drift" issue.

### Guidelines
- Query the logs using `get_system_logs`.
- Prompt the user to check if memory cleanup commands have had any effect, or track memory trends over multiple observation cycles.
