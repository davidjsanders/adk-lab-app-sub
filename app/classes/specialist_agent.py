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

"""Specialist agent class loading configuration and instructions from JSON resources."""

from functools import partial
import json
import logging
import os
import pathlib

from google.adk.agents import Agent
from google.adk.tools.skill_toolset import SkillToolset

from app.callbacks.specialist_state_loader import specialist_state_loader
from app.classes.global_gemini import GlobalGemini
from app.patches.patched_gcp_skill_registry import PatchedGCPSkillRegistry
from app.config import settings
from ..models.agent_categories import AgentCategories
from ..models.specialist_agent_config import SpecialistAgentConfig
from .mcp_helper import McpHelper
from .skills_helper import SkillsHelper
from .subagent_helper import SubagentHelper


# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class SpecialistAgent(Agent):
    """Generic Specialist Agent that loads its target system and instructions dynamically from config."""

    def __init__(self, config: SpecialistAgentConfig):
        """Initialize a SpecialistAgent by loading its metadata and instructions from config.

        Args:
            config: SpecialistAgentConfig instance containing agent configuration.
        """
        agent_name = config.name.lower().replace(' ', '_')
        mcp_tools = []
        agent_tools = []
        sub_agents = []

        # 1. Get tools
        if config.mcp_servers:
            mcp_helper = McpHelper(
                settings=settings,
                mcp_servers=config.mcp_servers
            )
            mcp_tools = mcp_helper.get_toolset()

        agent_tools = [*mcp_tools]
        # Initialize the skill registry pointing to the 'us' location
        # to avoid timeouts on regional skill endpoints in this environment.
        skill_registry = PatchedGCPSkillRegistry(
            project_id=settings.google_cloud_project,
            location="us"
        )

        # preloaded_skills = []
        # if config.skills:
        #     skills_helper = SkillsHelper(
        #         settings=settings,
        #         skills=config.skills
        #     )
        #     preloaded_skills = skills_helper.get_skills()

        # # Always register the SkillToolset with the registry to enable dynamic searching
        # system_skills = SkillToolset(
        #     skills=preloaded_skills,
        #     registry=skill_registry
        # )
        # agent_tools.append(system_skills)

        async def combined_before_agent_callback(callback_context):
            """Executes state loading and dynamic model routing before agent execution."""
            await specialist_state_loader(callback_context, target_systems=config.target_systems)
            # Dynamic Model Routing: Route to Pro model for complex planning/remediation tasks
            state = getattr(callback_context, "state", {})
            user_content = getattr(callback_context, "user_content", None)
            user_text = ""
            if user_content and hasattr(user_content, "parts") and user_content.parts:
                user_text = " ".join([p.text for p in user_content.parts if hasattr(p, "text") and p.text])
            elif state and "user_prompt" in state:
                user_text = str(state.get("user_prompt", ""))

            complex_keywords = ["remediate", "plan", "root cause", "architecture", "debug", "analyze"]
            agent_obj = getattr(callback_context, "agent", None) or getattr(callback_context, "node", None)
            if agent_obj and hasattr(agent_obj, "model"):
                target_model_name = settings.pro_model if any(kw in user_text.lower() for kw in complex_keywords) else settings.fast_model
                current_model_name = getattr(agent_obj.model, "model", "")
                if current_model_name != target_model_name:
                    logger.info("Dynamic Model Routing: Switching model from %s to %s", current_model_name, target_model_name)
                    agent_obj.model = GlobalGemini(model=target_model_name)

        async def human_in_the_loop_tool_callback(tool, args, tool_context=None):
            """Human-in-the-Loop hook requiring explicit operator confirmation before executing destructive operations."""
            high_stakes_keywords = ["restart", "reboot", "delete", "drop", "purge", "kill"]
            tool_name = getattr(tool, "name", str(tool)).lower()
            if any(keyword in tool_name for keyword in high_stakes_keywords):
                state = getattr(tool_context, "state", {}) if tool_context else {}
                if not state.get("human_approval_granted", False):
                    logger.warning("Human-in-the-Loop Hook: High-stakes action '%s' requires human confirmation", tool_name)
                    return (
                        f"STOP: High-stakes action '{tool_name}' requires explicit human operator confirmation. "
                        "Please ask the human operator for confirmation before proceeding."
                    )
            return None

        # 3. Initialize the ADK Agent
        super().__init__(
            name=f"sysman_{agent_name}_agent",
            model=GlobalGemini(model=settings.fast_model),
            description=config.description,
            instruction=config.instruction,
            tools=agent_tools,
            sub_agents=sub_agents,
            before_agent_callback=combined_before_agent_callback,
            before_tool_callback=human_in_the_loop_tool_callback,
        )
