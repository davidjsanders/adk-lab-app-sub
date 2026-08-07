---
name: common-reducing-memory-heap-usage
description: Diagnose and reduce Java JVM memory heap usage.
agent_types:
- Jira
categories:
- SaaS
- on-prem
license: Apache 2.0
---
# Reducing Memory Heap Usage Skill

Use this skill when JVM heap memory is elevated or there are OutOfMemory (OOM) warnings.

### Remediation Workflow
1. Execute `GC_CLEANUP` command on the Jira host (`jira-app-01`) to trigger Garbage Collection.
2. Verify status to check if JVM heap usage drops.
3. If memory continues to leak or remains critical, advise the orchestrator/user that a Jira restart is required.
