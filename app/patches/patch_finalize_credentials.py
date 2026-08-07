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

"""Patch for IAMConnectorCredentialsServiceClient.finalize_credentials to log A2A finalization mismatches."""

import logging
from google.cloud.iamconnectorcredentials_v1alpha import IAMConnectorCredentialsServiceClient

logger = logging.getLogger("sysman-agent.agent")


def patch_finalize_credentials() -> None:
    """Patches IAMConnectorCredentialsServiceClient.finalize_credentials to log A2A finalization mismatches."""
    _orig_finalize_credentials = IAMConnectorCredentialsServiceClient.finalize_credentials

    def _patched_finalize_credentials(self, request, *args, **kwargs):
        try:
            return _orig_finalize_credentials(self, request, *args, **kwargs)
        except Exception as e:
            msg = str(e)
            if "does not match the state user ID" in msg:
                logger.error(
                    "A2A User ID mismatch detected during finalization! "
                    f"Request User ID: '{request.user_id}'. "
                    "Ensure sub-agents have configured 'request_converter' to align user IDs."
                )
            raise e

    IAMConnectorCredentialsServiceClient.finalize_credentials = _patched_finalize_credentials
