import httpx
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from app.config import settings


def mcp_httpx_factory(**kwargs) -> httpx.AsyncClient:
    """Helper factory for creating async HTTPX clients for MCP server queries.

    Args:
        **kwargs: Arguments passed to httpx.AsyncClient.

    Returns:
        AsyncClient.
    """
    if "timeout" not in kwargs:
        kwargs["timeout"] = httpx.Timeout(45.0)
    return httpx.AsyncClient(**kwargs)


print(f"DEBUG: settings.mcp_server_url = {settings.mcp_server_url}")
# Initialize McpToolset with StreamableHTTPConnectionParams
mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=f"{settings.mcp_server_url.rstrip('/')}/mcp",
        httpx_client_factory=mcp_httpx_factory,
    )
)
