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

"""Patched GCP Skill Registry to fix HTTP 302 redirect handling."""

import logging
import httpx
from google.adk.integrations.skill_registry.gcp_skill_registry import GCPSkillRegistry
from google.adk.skills import models

logger = logging.getLogger(__name__)


class PatchedGCPSkillRegistry(GCPSkillRegistry):
    """Subclass of GCPSkillRegistry that overrides HTTP request and search behaviors.

    This patch addresses two issues:
    1. Sets follow_redirects=True in the httpx client to correctly resolve HTTP 302 redirects
       during skill payload downloads.
    2. Catches and skips Pydantic validation errors during skill search processing to prevent
       legacy or third-party registry skills with mismatched names or long descriptions from
       crashing search operations.
    """

    def _create_httpx_client(self) -> httpx.AsyncClient:
        """Creates an HTTP client with follow_redirects enabled.

        Returns:
            A configured AsyncClient instance for communicating with the Skill Registry API.
        """
        timeout = httpx.Timeout(30.0, connect=10.0)
        if self._ssl_context is not None:
            return httpx.AsyncClient(
                verify=self._ssl_context,
                follow_redirects=True,
                timeout=timeout,
            )
        return httpx.AsyncClient(follow_redirects=True, timeout=timeout)

    async def search_skills(self, *, query: str) -> list[models.Frontmatter]:
        """Searches for skills in the GCP registry.

        This method overrides the base implementation to gracefully catch and skip
        individual skill results that fail validation checks (e.g., due to invalid characters
        in the name or descriptions exceeding length limits), returning only valid matching skills.

        Args:
            query: The search query string.

        Returns:
            A list of validated Frontmatter objects representing the matching skills.
        """
        async with self._create_httpx_client() as client:
            url = (
                f"{self.base_url}/projects/{self.project_id}/"
                f"locations/{self.location}/skills:search"
            )
            params = {
                "search_string": query,
            }
            # pylint: disable=protected-access
            response = await self._make_request(client, url, params=params)
            response_data = response.json()

            results = []
            for s in response_data.get("skills", []):
                name = s.get("name", "").split("/")[-1]
                try:
                    results.append(
                        models.Frontmatter(
                            name=name,
                            description=s.get("description", "") or "",
                        )
                    )
                except Exception as e:
                    logger.warning(
                        "Skipping invalid skill '%s' in search results due to validation error: %s",
                        name,
                        e
                    )
            return results
