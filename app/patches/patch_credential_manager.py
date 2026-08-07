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

"""Patch for CredentialManager to fix ADK pre-auth callback ID bug and handle GCP sync delay."""

import asyncio
import logging
from google.adk.auth.credential_manager import CredentialManager

logger = logging.getLogger("sysman-agent.agent")


def patch_credential_manager() -> None:
    """Patches CredentialManager to fix ADK pre-auth callback ID bug and handle GCP sync delay."""
    _orig_get_auth_credential = CredentialManager.get_auth_credential

    async def _patched_get_auth_credential(self, context):
        if context.function_call_id is None:
            context.function_call_id = "_adk_toolset_auth_AgentRegistrySingleMcpToolset"
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(
                    "CredentialManager retrieving credentials for user_id: %s (function_call_id: %s)",
                    getattr(context, "user_id", None),
                    context.function_call_id,
                )
                res = await _orig_get_auth_credential(self, context)
                return res
            except RuntimeError as e:
                if "Failed to retrieve consent based credential" in str(e) and attempt < max_retries - 1:
                    logger.warning(
                        f"Credential retrieval failed (attempt {attempt+1}/{max_retries}). "
                        "GCP connector might be syncing. Retrying in 2 seconds..."
                    )
                    await asyncio.sleep(2)
                else:
                    raise e

    CredentialManager.get_auth_credential = _patched_get_auth_credential
