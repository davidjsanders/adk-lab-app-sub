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

"""Pydantic model class for Specialist Agent Configuration."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field
from app.models.agent_roles import AgentRoles


class SpecialistAgentConfig(BaseModel):
    """Configuration model representing a Specialist Agent configuration."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="The display name of the specialist agent")
    role: AgentRoles = Field(description="The role type of the agent (e.g. specialist)")
    description: str = Field(description="Description of what the agent does")
    instruction: str = Field(description="Detailed instructions / prompt template for the agent")
    categories: List[str] = Field(description="List of agent categories/prefixes managed")
    target_systems: List[str] = Field(
        alias="target-systems",
        description="List of target system IDs assigned to this specialist agent"
    )
    mcp_servers: List[str] = Field(
        default_factory=list,
        alias="mcp-servers",
        description="List of MCP server names referenced/used by this specialist agent"
    )
    skills: List[str] = Field(
        default_factory=list,
        description="List of skill names or search filters assigned to this specialist agent"
    )
    subagents: List[str] = Field(
        default_factory=list,
        description="List of sub-agent names to resolve and coordinate"
    )
