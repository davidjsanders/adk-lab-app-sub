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

"""Attach A2A (Agent2Agent) endpoints to the FastAPI app.

func:`attach_a2a_routes` registers the dynamic
agent-card endpoint and the JSON-RPC endpoint so the same app serves A2A
alongside the adk_api routes, reachable by A2A clients and Gemini Enterprise A2A
registration.
"""

from __future__ import annotations

import os
import logging
from typing import TYPE_CHECKING

logger = logging.getLogger("sysman-agent.agent")

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import TaskStore
from a2a.types import AgentCapabilities, AgentExtension
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.executor.config import A2aAgentExecutorConfig
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

from app.helpers.a2ui_interceptor import a2ui_converter_interceptor

if TYPE_CHECKING:
    from fastapi import FastAPI
    from google.adk.agents import BaseAgent
    from google.adk.runners import Runner

# URI advertised on the agent card describing the executor extension shipped
# by ADK. Kept as a module-level constant so callers can override or extend
# the capabilities list when needed.
_ADK_AGENT_EXECUTOR_EXTENSION_URI = (
    "https://google.github.io/adk-docs/a2a/a2a-extension/"
)


def _default_capabilities() -> AgentCapabilities:
    """Returns the default A2A capabilities used by scaffolded projects."""
    return AgentCapabilities(
        streaming=True,
        extensions=[
            AgentExtension(
                uri="https://a2ui.org/a2a-extension/a2ui/v0.8",
                description="Ability to render A2UI",
                params={
                    "supportedCatalogIds": [
                        "https://a2ui.org/specification/v0_8/standard_catalog_definition.json"
                    ]
                },
            ),
            AgentExtension(
                uri=_ADK_AGENT_EXECUTOR_EXTENSION_URI,
                description=("Ability to use the new agent executor implementation"),
            ),
        ],
    )


async def attach_a2a_routes(
    app: FastAPI,
    *,
    agent: BaseAgent,
    runner: Runner,
    task_store: TaskStore,
    rpc_path: str,
    capabilities: AgentCapabilities | None = None,
    agent_version: str | None = None,
    app_url: str | None = None,
) -> None:
    """Register A2A routes (JSON-RPC + agent-card endpoints) under ``rpc_path``.

    Builds a dynamic agent card from ``agent`` and mounts the routes on ``app``.
    The ``runner`` should share the session/artifact/memory services with the
    standard ADK path. ``capabilities``, ``agent_version``, and ``app_url``
    override their defaults (streaming + ADK extension, ``AGENT_VERSION``,
    ``APP_URL``). Call once per app — typically in a FastAPI ``lifespan``, since
    the card is built asynchronously; repeated calls register duplicate routes.
    """
    resolved_app_url = app_url or os.getenv("APP_URL") or f"http://127.0.0.1:{os.getenv('PORT', '8000')}"
    resolved_agent_version = agent_version or os.getenv("AGENT_VERSION", "0.1.0")
    resolved_capabilities = capabilities or _default_capabilities()

    agent_card = await AgentCardBuilder(
        agent=agent,
        capabilities=resolved_capabilities,
        rpc_url=f"{resolved_app_url}{rpc_path}",
        agent_version=resolved_agent_version,
    ).build()

    from google.adk.a2a.converters.request_converter import convert_a2a_request_to_agent_run_request

    def _custom_request_converter(request, part_converter):
        run_req = convert_a2a_request_to_agent_run_request(request, part_converter)
        # Override the dynamic A2A user ID with the playground's active user ID to align for 3LO consent
        run_req.user_id = os.getenv("PLAYGROUND_USER_ID", "user")
        logger.info("A2A Request converted. run_req.user_id: %s (PLAYGROUND_USER_ID env: %s)", run_req.user_id, os.getenv("PLAYGROUND_USER_ID"))
        return run_req

    executor_config = A2aAgentExecutorConfig(
        request_converter=_custom_request_converter,
        execute_interceptors=[
            a2ui_converter_interceptor,
        ]
    )

    request_handler = DefaultRequestHandler(
        agent_executor=A2aAgentExecutor(runner=runner, config=executor_config),
        task_store=task_store,
    )

    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)
    a2a_app.add_routes_to_app(
        app,
        agent_card_url=f"{rpc_path}{AGENT_CARD_WELL_KNOWN_PATH}",
        rpc_url=rpc_path,
        extended_agent_card_url=f"{rpc_path}{EXTENDED_AGENT_CARD_PATH}",
    )
