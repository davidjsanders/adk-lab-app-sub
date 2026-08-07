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

"""Helper function to load and validate specialist agent configurations."""

import json
import os

from ..classes.settings import Settings
from ..models.specialist_agent_config import SpecialistAgentConfig


def load_agent_config(settings: Settings) -> SpecialistAgentConfig:
    """Loads the agent configuration from the JSON file path specified in settings.

    Args:
        settings: The settings container containing the configured config file.

    Returns:
        The validated SpecialistAgentConfig model instance.

    Raises:
        FileNotFoundError: If the configured agent config file does not exist.
        ValueError: If the config JSON fails to validate against the SpecialistAgentConfig schema.
    """
    config_file = settings.agent_config_file

    # Resolve the config file path if it's relative
    if not os.path.isabs(config_file):
        candidates = [
            config_file,
            os.path.join(os.path.dirname(__file__), "..", "resources", config_file),
            os.path.join(os.path.dirname(__file__), "..", "..", config_file),
        ]
        for candidate in candidates:
            resolved = os.path.abspath(candidate)
            if os.path.exists(resolved):
                config_file = resolved
                break

    if not os.path.exists(config_file):
        raise FileNotFoundError(
            f"Configured agent configuration file not found: {settings.agent_config_file} "
            f"(resolved path: {config_file})"
        )

    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return SpecialistAgentConfig.model_validate(data)
