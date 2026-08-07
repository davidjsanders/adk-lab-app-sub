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

"""Initialization module for agent patches."""

from .patch_credential_manager import patch_credential_manager
from .patch_finalize_credentials import patch_finalize_credentials
from .patched_gcp_skill_registry import PatchedGCPSkillRegistry

__all__ = [
    "patch_credential_manager",
    "patch_finalize_credentials",
    "PatchedGCPSkillRegistry",
]
