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

"""SubagentHelper provides simplified retrieval of sub-agents from Agent Registry."""

import logging
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from .registry_helper import RegistryHelper
from ..models.registry_resource_type import RegistryResourceType
from ..models.settings import Settings

logger = logging.getLogger(__name__)


class SubagentHelper:
    """Helper wrapper for fetching sub-agents from GCP Agent Registry."""

    def __init__(
        self,
        settings: Settings,
        subagents: list[str],
    ) -> None:
        """Initialize a SubagentHelper.

        Args:
            settings: The agent Settings object.
            subagents: A list of sub-agent display names to resolve.
        """
        self.settings = settings
        self.registry_helper = RegistryHelper(
            self.settings.google_cloud_project,
            self.settings.google_cloud_location
        )
        self.subagents = subagents
        self.resolved_agents: list[RemoteA2aAgent] = []

    def get_subagents(self) -> list[RemoteA2aAgent]:
        """Fetch and return the resolved RemoteA2aAgent objects from the registry.

        Returns:
            A list of resolved RemoteA2aAgent objects matching the configured names.

        Raises:
            ValueError: If a sub-agent is not found or multiple match a given name.
        """
        if not self.subagents:
            return []

        self.resolved_agents = []
        for name in self.subagents:
            resources = self.registry_helper.find(
                display_name=name,
                resource_type=RegistryResourceType.AGENT,
            )
            if not resources:
                raise ValueError(
                    f"Sub-agent '{name}' not found in registry"
                )
            if len(resources) > 1:
                # If multiple are found, match by display name or registry id suffix
                # For safety, raise exception or log warning. Let's raise error for ambiguity.
                raise ValueError(
                    f"Multiple sub-agents found with name '{name}'"
                )

            agent_urn = resources[0].get("name", "")
            resolved_agent = self.registry_helper.get(
                registered_name=agent_urn,
                resource_type=RegistryResourceType.AGENT,
            )
            if not resolved_agent:
                raise ValueError(
                    f"Sub-agent '{agent_urn}' could not be resolved from registry"
                )
            self.resolved_agents.append(resolved_agent)

        return self.resolved_agents
