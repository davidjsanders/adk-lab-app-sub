# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Custom native Python tools with strict Pydantic schemas and guided error handling."""

import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SystemHealthQuery(BaseModel):
    """Strict input schema for system health diagnostic queries."""

    system_id: str = Field(
        ...,
        description="The unique identifier of the target system (e.g., 'jira-app-01', 'confluence-app-01', 'linux-server-01')."
    )
    metric_category: Optional[str] = Field(
        default="all",
        description="Optional telemetry metric category to query (e.g., 'cpu', 'memory', 'heap', 'latency', 'all')."
    )


class SystemHealthReport(BaseModel):
    """Strict output schema representing system health status."""

    system_id: str
    status: str
    heap_usage_pct: float
    latency_ms: float
    cpu_load_pct: float
    recommendation: str


def inspect_system_health(query: SystemHealthQuery) -> str:
    """Diagnoses system operational health metrics and returns guided recommendations.

    Args:
        query: SystemHealthQuery model specifying system_id and metric_category.

    Returns:
        JSON string or guided recovery response message for the LLM.
    """
    logger.info(
        "Executing inspect_system_health tool for target system: %s (category: %s)",
        query.system_id,
        query.metric_category,
        extra={"intent": "diagnose_system_health", "outcome": "in_progress"}
    )
    try:
        if not query.system_id:
            raise ValueError("system_id must be provided to query system health.")

        report = SystemHealthReport(
            system_id=query.system_id,
            status="HEALTHY",
            heap_usage_pct=72.4,
            latency_ms=450.0,
            cpu_load_pct=38.2,
            recommendation="System operating within normal parameters. No immediate remediation required."
        )

        logger.info(
            "Successfully generated system health report for %s",
            query.system_id,
            extra={"intent": "diagnose_system_health", "outcome": "success"}
        )
        return report.model_dump_json()

    except Exception as e:
        logger.error(
            "Error inspecting health for system %s: %s",
            query.system_id,
            e,
            extra={"intent": "diagnose_system_health", "outcome": "failed"}
        )
        return (
            f"ERROR: Failed to query system health for '{query.system_id}': {e}. "
            "GUIDED RECOVERY: Verify that the system_id is valid (e.g., 'jira-app-01', 'confluence-app-01', 'linux-server-01') "
            "and retry using tool 'inspect_system_health' with valid parameters."
        )
