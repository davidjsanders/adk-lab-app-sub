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

"""SkillsHelper provides simplified retrieval of skills from Agent Registry."""

import asyncio
from google.adk.skills.models import Skill

from .registry_helper import RegistryHelper
from ..models.registry_resource_type import RegistryResourceType
from ..models.settings import Settings


class SkillsHelper:
    """Helper wrapper for fetching Agent Skills from GCP Agent Registry."""

    def __init__(
        self,
        settings: Settings,
        skills: list[str],
    ) -> None:
        """Initialize a SkillsHelper.

        Args:
            settings: The agent Settings object.
            skills: A list of skill names to resolve.
        """
        self.settings = settings
        self.registry_helper = RegistryHelper(
            self.settings.google_cloud_project,
            self.settings.google_cloud_location
        )
        self.skills = skills
        self.resolved_skills: list[Skill] = []

    def get_skills(self) -> list[Skill]:
        """Fetch and return the resolved Skill objects from the registry.

        Returns:
            A list of resolved Skill objects matching the configured skill names.

        Raises:
            ValueError: If a skill is not found or multiple match a given name.
        """
        if not self.skills:
            return []

        self.resolved_skills = []
        urns_to_resolve: list[str] = []
        seen_urns: set[str] = set()

        for skill_name in self.skills:
            if skill_name.startswith("projects/"):
                if skill_name not in seen_urns:
                    urns_to_resolve.append(skill_name)
                    seen_urns.add(skill_name)
                continue

            resources = self.registry_helper.find(
                display_name=skill_name,
                resource_type=RegistryResourceType.SKILL,
            )
            if not resources:
                raise ValueError(
                    f"Skill '{skill_name}' not found in registry"
                )

            for resource in resources:
                urn = resource.get("name", "")
                if urn and urn not in seen_urns:
                    # Filter to make sure the search query is actually part of the skill ID segment
                    short_name = urn.split("/")[-1]
                    if skill_name in short_name:
                        urns_to_resolve.append(urn)
                        seen_urns.add(urn)

        if not urns_to_resolve:
            return []

        async def _resolve_all():
            tasks = [
                self.registry_helper.get_skill_async(urn)
                for urn in urns_to_resolve
            ]
            return await asyncio.gather(*tasks)

        skills = self.registry_helper._run_async(_resolve_all())
        for urn, skill in zip(urns_to_resolve, skills):
            if skill is None:
                raise ValueError(
                    f"Skill '{urn}' could not be resolved from registry"
                )
            self.resolved_skills.append(skill)

        return self.resolved_skills
