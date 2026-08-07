import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from ..models.agent_roles import AgentRoles
from ..models.agent_categories import AgentCategories


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Logging
    log_level: str = Field(
        default=os.environ.get("LOG_LEVEL", "INFO").upper(),
        validation_alias="LOG_LEVEL"
    )

    # Google specific
    impersonate_sa: str = Field(
        default="",
        validation_alias="IMPERSONATE_SA"
    )

    # GCP Configuration
    google_cloud_project: str = Field(
        ...,
        validation_alias="GOOGLE_CLOUD_PROJECT"
    )
    google_cloud_location: str = Field(
        ...,
        validation_alias="GOOGLE_CLOUD_LOCATION"
    )
    google_genai_use_vertexai: bool = Field(
        default=True,
        validation_alias="GOOGLE_GENAI_USE_VERTEXAI"
    )

    # Model definitions
    fast_model: str = Field(
        default="gemini-3-flash-preview",
        validation_alias="FAST_MODEL"
    )
    pro_model: str = Field(
        default="gemini-3.1-pro-preview",
        validation_alias="PRO_MODEL"
    )

    # SysMan Infrastructure
    mcp_server_url: str = Field(
        default="http://127.0.0.1:8005",
        validation_alias="MCP_SERVER_URL"
    )

    skills_cache_dir: Optional[str] = Field(
        default=".skills_cache",
        validation_alias="SKILLS_CACHE_DIR"
    )

    # Vertex AI Search (for Diagnosis Agent)
    vai_search_project: str = Field(
        default="",
        validation_alias="VERTEX_AI_SEARCH_PROJECT"
    )
    vai_search_location: str = Field(
        default="global",
        validation_alias="VERTEX_AI_SEARCH_LOCATION"
    )
    vai_search_data_store_id: str = Field(
        default="",
        validation_alias="VERTEX_AI_SEARCH_DATA_STORE_ID"
    )

    # Agent specific
    agent_config_file: str = Field(
        default="agents.json",
        validation_alias="AGENT_CONFIG_FILE"
    )
    agent_registry_suffix: str = Field(
        default="dev",
        validation_alias="AGENT_REGISTRY_SUFFIX"
    )
