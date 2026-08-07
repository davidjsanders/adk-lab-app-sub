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

"""Callback for loading specialist agent state variables."""

from google.adk.agents.callback_context import CallbackContext


async def specialist_state_loader(callback_context: CallbackContext, target_systems: list[str]) -> None:
    """Callback hook that loads system configuration variables into the agent session state.

    Args:
        callback_context: The ADK callback context.
        target_systems: A list of target system IDs managed by this agent.
    """
    callback_context.state["target_system_id"] = target_systems