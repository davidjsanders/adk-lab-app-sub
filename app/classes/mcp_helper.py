from .registry_helper import RegistryHelper
from ..models.registry_resource_type import RegistryResourceType
from ..models.settings import Settings


class McpHelper:
    def __init__(
        self,
        settings: Settings,
        mcp_servers: list[str]
    ):
        """Initialize a McpHelper.

        Args:
            settings: The agent Settings object.
            mcp_servers: A list of MCP server names.
        """
        self.settings = settings
        self.registry_helper = RegistryHelper(
            self.settings.google_cloud_project,
            self.settings.google_cloud_location
        )
        self.mcp_servers = mcp_servers
        self.toolsets = []

    def get_toolset(self):
        if not self.mcp_servers:
            return None

        self.toolsets = []
        for server in self.mcp_servers:
            resources = self.registry_helper.find(
                display_name=server,
                resource_type=RegistryResourceType.MCP,
            )
            if not resources:
                raise ValueError(
                    f"MCP server '{server}' not found in registry"
                )
            if len(resources) > 1:
                raise ValueError(
                    f"Multiple MCP servers found with display name '{server}'"
                )

            mcp_server = self.registry_helper.get(
                registered_name=resources[0].get("name", ""),
                resource_type=RegistryResourceType.MCP,
                continue_uri=self.settings.continue_uri,
            )
            self.toolsets.append(mcp_server)

        return self.toolsets
