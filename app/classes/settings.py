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

    # GCP & Agent configs
    google_cloud_project: str = Field(
        default="agentspace-argolis-demo",
        validation_alias="GOOGLE_CLOUD_PROJECT"
    )
    google_cloud_location: str = Field(
        default="us-central1",
        validation_alias="GOOGLE_CLOUD_LOCATION"
    )
    google_genai_use_vertexai: bool = Field(
        default=True,
        validation_alias="GOOGLE_GENAI_USE_VERTEXAI"
    )

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
        default="http://127.0.0.1:8002",
        validation_alias="MCP_SERVER_URL"
    )

    # Detection Agent Skills (comma-separated list of loaded skills)
    detection_skills: str = Field(
        default="anomaly-detection,baseline-learning,drift-detection,alert-dedup,jira-ops,confluence-ops",
        validation_alias="DETECTION_SKILLS"
    )

    # Dynamic Agent settings
    agent_role: AgentRoles = Field(
        default=AgentRoles.ORCHESTRATOR,
        validation_alias="AGENT_ROLE"
    )

    agent_categories: list[AgentCategories] = Field(
        default=[AgentCategories.LINUX],
        validation_alias="AGENT_CATEGORIES"
    )
    agent_config_file: str = Field(
        ...,
        validation_alias="AGENT_CONFIG_FILE"
    )

    agent_registry_suffix: str = Field(
        default="dev",
        validation_alias="AGENT_REGISTRY_SUFFIX"
    )
    impersonate_sa: str = Field(
        default="",
        validation_alias="IMPERSONATE_SA"
    )
    skills_cache_dir: Optional[str] = Field(
        default=".skills_cache",
        validation_alias="SKILLS_CACHE_DIR"
    )
    continue_uri: Optional[str] = Field(
        default=None,
        validation_alias="CONTINUE_URI"
    )



    # Vertex AI Search (for Diagnosis Agent)
    vertex_ai_search_project: str = Field(
        default="",
        validation_alias="VERTEX_AI_SEARCH_PROJECT"
    )
    vertex_ai_search_location: str = Field(
        default="global",
        validation_alias="VERTEX_AI_SEARCH_LOCATION"
    )
    vertex_ai_search_data_store_id: str = Field(
        default="",
        validation_alias="VERTEX_AI_SEARCH_DATA_STORE_ID"
    )
