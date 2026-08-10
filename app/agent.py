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

"""Sysman agent entrypoint module for initializing and starting the agent app."""

import logging
from google.adk.apps import App
from google.adk.auth.credential_manager import CredentialManager
from google.adk.integrations.agent_identity import GcpAuthProvider
from .classes.specialist_agent import SpecialistAgent
from .helpers import logging_config
from .helpers.config import agent_config
from .plugins.a2ui_plugin import A2UIPlugin
from .patches.patch_credential_manager import patch_credential_manager
from .patches.patch_finalize_credentials import patch_finalize_credentials

logging_config.setup_logging()
logger = logging.getLogger("sysman-agent.agent")

# Register the GCP Auth Provider to resolve credentials for MCP toolsets
CredentialManager.register_auth_provider(GcpAuthProvider())

# Patch CredentialManager to work around ADK pre-auth bugs
# See the readme in the patches/ folder.
patch_credential_manager()
patch_finalize_credentials()

# Shared A2UI Plugin instance for handling A2UI Components
a2ui_plugin = A2UIPlugin()

# Initialize the root agent (depends on role)
logger.info(f"Starting SysMan Agent in role: {agent_config.role}")
root_agent = SpecialistAgent(config=agent_config)

# Initialize the App
app = App(
    root_agent=root_agent,
    name="app",
    plugins=[a2ui_plugin],
)
