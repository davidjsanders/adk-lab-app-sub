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

"""RegistryHelper provides simplified resource retrieval and discovery from GCP Agent Registry."""

import asyncio
import contextvars
import logging
import os
import threading
from typing import Any, Dict, List, Optional, Union
from requests.exceptions import HTTPError

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.auth.credential_manager import CredentialManager
from google.adk.integrations.agent_registry import AgentRegistry
from google.adk.integrations.agent_identity import GcpAuthProvider
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.skills.models import Skill

from ..models.registry_resource_type import RegistryResourceType
from app.patches.patched_gcp_skill_registry import PatchedGCPSkillRegistry

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class RegistryHelper:
    """Helper wrapper around GCP Agent Registry and Skill Registry clients.

    Provides a uniform API to find (list/search) and get (retrieve by ID)
    registered resources such as A2A Agents, MCP Servers, Model Endpoints,
    and Agent Skills.
    """

    def __init__(
        self,
        project_id: str,
        location: str,
    ) -> None:
        """Initialize the RegistryHelper.

        Args:
            project_id: The Google Cloud project ID.
            location: The Google Cloud region/location.
        """
        # Ensure Vertex AI integration is active
        logger.debug("Initializing registry helper")
        if not os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", None):
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
        self._location = location
        self._project_id = project_id

        # Instantiate standard AgentRegistry client
        logger.debug("RegistryHelper project_id: %s", self._project_id)
        logger.debug("RegistryHelper location: %s", self._location)
        self._registry = AgentRegistry(
            project_id=self._project_id,
            location=self._location,
        )
        logger.debug("registry initialized?: %s", True if self._registry else "None!")

    @property
    def registry(self) -> AgentRegistry:
        """The underlying AgentRegistry client instance."""
        return self._registry

    @property
    def location(self) -> str:
        """The configured location/region."""
        return self._location

    @property
    def project_id(self) -> str:
        """The configured GCP project ID."""
        return self._project_id

    def find(
        self,
        display_name: str,
        resource_type: RegistryResourceType,
    ) -> List[Dict[str, Any]]:
        """Search or list resources matching a display name or keyword.

        Args:
            display_name: Keyword/search expression (e.g. "confluence" or "displayName:confluence*").
            resource_type: The type of resource to search for.

        Returns:
            A list of dictionary objects representing the metadata of matching resources.

        Raises:
            ValueError: If an unknown resource type is requested.
            RuntimeError: If the registry request fails.
        """
        try:
            match resource_type:
                case RegistryResourceType.AGENT:
                    logger.debug("Looking for agent: %s", display_name)
                    # Fetch list of matching agents using ADK client
                    _found_agents = self.registry.list_agents(
                        filter_str=display_name or ""
                    )
                    return self._find_tool(
                        results=_found_agents,
                        key_str=RegistryResourceType.AGENT.value
                    )

                case RegistryResourceType.MCP:
                    logger.debug("Looking for mcp: %s", display_name)
                    # Fetch list of matching MCP servers using ADK client
                    _found_mcp_servers = self.registry.list_mcp_servers(
                        filter_str=display_name or ""
                    )
                    logger.debug("Found: %s", _found_mcp_servers)
                    return self._find_tool(
                        results=_found_mcp_servers,
                        key_str=RegistryResourceType.MCP.value
                    )
                case RegistryResourceType.ENDPOINT:
                    logger.debug("Looking for endpoint: %s", display_name)
                    # Fetch list of matching endpoints using ADK client
                    _found_endpoints = self.registry.list_endpoints(
                        filter_str=display_name or ""
                    )
                    return self._find_tool(
                        results=_found_endpoints,
                        key_str=RegistryResourceType.ENDPOINT.value
                    )

                case RegistryResourceType.SKILL:
                    logger.debug("Looking for skill: %s", display_name)
                    # Override location to "us" if it's regional (e.g. us-central1)
                    # because skills in this environment are only hosted and served in the "us" region.
                    # Regional endpoints for skills search currently hang and time out.
                    skill_location = self.location
                    if skill_location != "us":
                        logger.warning(
                            "Overriding skills search location from '%s' to 'us' to prevent timeouts.",
                            skill_location,
                        )
                        skill_location = "us"

                    # Instantiate custom skill registry wrapper to fetch skills
                    skill_reg = PatchedGCPSkillRegistry(
                        project_id=self.project_id, location=skill_location
                    )

                    async def _search_skills_async():
                        async with skill_reg._create_httpx_client() as client:
                            headers = await skill_reg._get_headers()
                            # Use /skills:search endpoint if search query is provided
                            if display_name:
                                url = (
                                    f"{skill_reg.base_url}/projects/{skill_reg.project_id}/"
                                    f"locations/{skill_reg.location}/skills:search"
                                )
                                params = {"search_string": display_name}
                            # Otherwise list all skills via base /skills endpoint
                            else:
                                url = (
                                    f"{skill_reg.base_url}/projects/{skill_reg.project_id}/"
                                    f"locations/{skill_reg.location}/skills"
                                )
                                params = {}

                            # Make request using HTTP client configured with SSL contexts and custom timeouts
                            response = await client.get(
                                url, headers=headers, params=params
                            )
                            if response.status_code == 200:
                                return response.json()
                            else:
                                raise RuntimeError(
                                    f"Skill search failed: {response.status_code} - {response.text}"
                                )

                    # Run async request synchronously within current context
                    _found_skills = self._run_async(_search_skills_async())
                    return self._find_tool(
                        results=_found_skills,
                        key_str=RegistryResourceType.SKILL.value
                    )
                case _:
                    raise ValueError(f"Unknown resource type: {resource_type}")
        except Exception as e:
            logger.error(
                "Error finding %s: %s - %s", 
                resource_type.value[:-1],
                display_name, 
                e
            )
            raise e

    def get(
        self,
        registered_name: str,
        resource_type: RegistryResourceType,
        continue_uri: Optional[str] = None,
    ) -> Union[RemoteA2aAgent, McpToolset, Dict[str, Any], Skill, None]:
        """Retrieve a specific resource instance by its URN or relative name.

        Args:
            registered_name: The resource ID or fully qualified resource name.
            resource_type: The type of resource to fetch.
            continue_uri: Optional redirection URI for 3-legged OAuth consent flows.

        Returns:
            The resolved resource instance (e.g. RemoteA2aAgent, McpToolset, etc.),
            or None if the resource was not found (404).

        Raises:
            ValueError: If an unknown resource type is specified.
            RuntimeError: If retrieval fails.
        """
        try:
            match resource_type:
                case RegistryResourceType.AGENT:
                    registered_name = self._full_resource_id(
                        registered_name,
                        RegistryResourceType.AGENT
                    )
                    logger.debug("Looking up agent: %s", registered_name)
                    # Returns instantiated RemoteA2aAgent wrapper ready to use
                    return self.registry.get_remote_a2a_agent(
                        agent_name=registered_name
                    )

                case RegistryResourceType.MCP:
                    registered_name = self._full_resource_id(
                        registered_name,
                        RegistryResourceType.MCP
                    )
                    logger.debug("Looking up MCP: %s", registered_name)

                    use_dynamic_adc = os.environ.get("USE_ADK_DYNAMIC_ADC_AUTH", "true").lower() == "true"
                    logger.debug("MCP auth resolution - USE_ADK_DYNAMIC_ADC_AUTH: %s", use_dynamic_adc)

                    auth_scheme = None
                    auth_credential = None

                    if use_dynamic_adc:
                        try:
                            server_details = self.registry.get_mcp_server(registered_name)
                            endpoint_uri, _, _ = self.registry._get_connection_uri(server_details)
                            logger.debug("Resolved MCP endpoint_uri for dynamic auth: %s", endpoint_uri)

                            from app.helpers.mcp_auth_helper import get_mcp_auth
                            auth_scheme, auth_credential = get_mcp_auth(endpoint_uri)
                            logger.debug("get_mcp_auth returned auth_scheme: %s, auth_credential: %s", auth_scheme, auth_credential)

                            if not auth_scheme:
                                logger.debug("No custom auth_scheme returned; registering default GcpAuthProvider")
                                CredentialManager.register_auth_provider(GcpAuthProvider())
                        except Exception as e:
                            logger.warning(
                                "Failed to configure custom ADK auth for MCP server '%s', falling back: %s", 
                                registered_name, 
                                e
                            )
                            CredentialManager.register_auth_provider(GcpAuthProvider())
                    else:
                        logger.info("Using standard GCP Auth Provider for MCP server (dynamic auth disabled)")
                        CredentialManager.register_auth_provider(GcpAuthProvider())

                        # Manually configure the GcpAuthProviderScheme for local testing
                        from google.adk.integrations.agent_identity import GcpAuthProviderScheme
                        auth_scheme = GcpAuthProviderScheme(
                            name=f"projects/{self._project_id}/locations/{self._location}/connectors/sysman-oauth",
                            scopes=["https://www.googleapis.com/auth/cloud-platform"],
                            continue_uri=os.environ.get("CONTINUE_URI", "http://127.0.0.1:8000/oauth-callback"),
                        )
                        logger.debug("Configured manual GcpAuthProviderScheme: %s", auth_scheme)

                        # In local dev environment, add X-Serverless-Authorization for Cloud Run IAM transport
                        impersonate_sa = os.environ.get("IMPERSONATE_SA")
                        logger.debug("IMPERSONATE_SA env var: %s", impersonate_sa)
                        if impersonate_sa:
                            try:
                                server_details = self.registry.get_mcp_server(registered_name)
                                endpoint_uri, _, _ = self.registry._get_connection_uri(server_details)
                                from app.helpers.mcp_auth_helper import generate_impersonated_id_token

                                from urllib.parse import urlparse
                                parsed_url = urlparse(endpoint_uri)
                                target_audience = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                logger.debug("Calculated target_audience for impersonation: %s", target_audience)

                                def _local_header_provider(context):
                                    logger.debug("Executing _local_header_provider for SA %s (audience: %s)", impersonate_sa, target_audience)
                                    token = generate_impersonated_id_token(impersonate_sa, target_audience)
                                    if token:
                                        logger.debug("Successfully generated impersonated ID token (length: %d)", len(token))
                                        return {"X-Serverless-Authorization": f"Bearer {token}"}
                                    logger.warning("Failed to generate impersonated ID token for SA %s", impersonate_sa)
                                    return {}

                                self.registry._header_provider = _local_header_provider
                                logger.info("Configured X-Serverless-Authorization header provider for local Cloud Run transport (audience: %s)", target_audience)
                            except Exception as e:
                                logger.warning("Could not set local transport header provider: %s", e)

                    # Returns McpToolset containing all registered tools on the server
                    logger.debug("Retrieving McpToolset for %s (auth_scheme=%s, continue_uri=%s)", registered_name, auth_scheme, continue_uri)
                    if continue_uri:
                        return self.registry.get_mcp_toolset(
                            registered_name,
                            auth_scheme=auth_scheme,
                            auth_credential=auth_credential,
                            continue_uri=continue_uri
                        )
                    return self.registry.get_mcp_toolset(
                        registered_name,
                        auth_scheme=auth_scheme,
                        auth_credential=auth_credential
                    )

                case RegistryResourceType.ENDPOINT:
                    registered_name = self._full_resource_id(
                        registered_name,
                        RegistryResourceType.ENDPOINT
                    )
                    logger.debug("Looking up Endpoint: %s", registered_name)
                    # Returns dict representing endpoint interfaces and properties
                    return self.registry.get_endpoint(
                        registered_name
                    )

                case RegistryResourceType.SKILL:
                    return self._run_async(self.get_skill_async(registered_name))
                case _:
                    raise ValueError(f"Unknown resource type: {resource_type}")
        except RuntimeError as e:
            root_error = e.__cause__
            # Intercept HTTP 404 errors to return None instead of raising exceptions
            if isinstance(root_error, HTTPError):
                if root_error.response.status_code == 404:
                    logger.warning(
                        "Could not find %s: %s", 
                        resource_type.value[:-1],
                        registered_name
                    )
                    return None

            logger.error(
                "Error getting %s: %s - %s", 
                resource_type.value[:-1],
                registered_name, 
                e
            )
            raise e
        except Exception as e:
            logger.error(
                "Error getting %s: %s - %s", 
                resource_type.value[:-1],
                registered_name, 
                e
            )
            raise e

    async def get_skill_async(
        self,
        registered_name: str,
    ) -> Optional[Skill]:
        """Asynchronously retrieve a skill from the registry.

        Args:
            registered_name: The resource ID or fully qualified resource name.

        Returns:
            The resolved Skill instance, or None if not found.
        """
        registered_name = self._full_resource_id(
            registered_name,
            RegistryResourceType.SKILL
        )
        logger.debug("Looking up skill: %s", registered_name)

        project_id = self.project_id
        location = self.location
        if registered_name.startswith("projects/"):
            parts = registered_name.split("/")
            if len(parts) >= 4 and parts[0] == "projects" and parts[2] == "locations":
                project_id = parts[1]
                location = parts[3]

        skill_reg = PatchedGCPSkillRegistry(
            project_id=project_id,
            location=location
        )
        short_name = self._short_resource_id(registered_name)
        return await skill_reg.get_skill(name=short_name)

    def _find_tool(self, results: dict, key_str: str) -> List[Dict[str, Any]]:
        """Extract list items from search results dictionary safely.

        Args:
            results: The API response payload.
            key_str: Key containing the array list (e.g. "skills", "agents").

        Returns:
            The list of extracted resource dictionary metadata.
        """
        if not results:
            return []
        if not results.get(key_str, None):
            return []

        return results[key_str]

    def _full_resource_id(
        self,
        resource_id: str,
        resource_key: RegistryResourceType,
    ) -> str:
        """Convert short resource IDs into fully-qualified GCP resource names.

        Args:
            resource_id: The relative name or short ID.
            resource_key: The resource type.

        Returns:
            Fully-qualified URN string: projects/{project}/locations/{location}/{resource_type}/{resource_id}.
        """
        if resource_id.startswith("projects"):
            return resource_id

        return (
            f"projects/{self.project_id}/"
            f"locations/{self.location}/"
            f"{resource_key.value}/{resource_id}"
        )

    def _short_resource_id(
        self,
        resource_id: str,
    ) -> str:
        """Extract the final leaf ID segment from a fully-qualified resource name.

        Args:
            resource_id: The resource name string.

        Returns:
            The leaf segment identifier.
        """
        if resource_id.startswith("projects"):
            return resource_id.split("/")[-1]

        return resource_id

    def _run_async(self, coro) -> Any:
        """Run a coroutine synchronously, safely handling existing event loops.

        Args:
            coro: The async coroutine to execute.

        Returns:
            The return value of the coroutine.
        """
        try:
            # Check if there is an active event loop in the current thread
            asyncio.get_running_loop()
            # If so, run it in a separate thread to avoid "event loop already running" error
            ctx = contextvars.copy_context()
            result = []
            error = []

            def target():
                try:
                    # Run inside the copied context to preserve thread-local context variables
                    res = ctx.run(asyncio.run, coro)
                    result.append(res)
                except Exception as e:
                    error.append(e)

            thread = threading.Thread(target=target)
            thread.start()
            thread.join()

            if error:
                raise error[0]
            return result[0]
        except RuntimeError:
            # No running event loop in this thread, safe to use standard asyncio.run
            return asyncio.run(coro)
