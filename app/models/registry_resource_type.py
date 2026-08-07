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

"""Registry resource type enum definition."""

from enum import Enum


class RegistryResourceType(Enum):
    """Enum representing the different types of resources in the Agent Registry."""

    AGENT = "agents"
    MCP = "mcpServers"
    ENDPOINT = "endpoints"
    SKILL = "skills"
