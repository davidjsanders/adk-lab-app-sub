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

import json
import logging
import re
from typing import Any, Optional

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.plugins import BasePlugin
from google.adk.tools import BaseTool, ToolContext
from google.genai import types

logger = logging.getLogger("sysman-detection-agent.plugins.a2ui")
logger.setLevel(level=logging.DEBUG) # FORCE debug


class A2UIPlugin(BasePlugin):
    """Plugin that intercepts A2UI card outputs and returns them
    directly to the agent for rendering.

    Bypasses the normal LLM summarization behavior AND interrupts
    the current turn (by not returning anything to the LLM).

    AN IMPORTANT NOTE: If more than one card is returned in a turn,
    the cards are queued for rendering so that they are all successfully
    intercepted and returned in the on_event_callback.

    Example:
        a2ui_plugin = A2UIPlugin()

        root_agent = Agent(config=agent_config)

        app = App(
            root_agent=root_agent,
            name="app",
            plugins=[a2ui_plugin],
        )
    """

    def __init__(self, name: str = "a2ui_plugin") -> None:
        super().__init__(name=name)
        self._pending_cards: dict[str, list[str]] = {}

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: Any,
    ) -> Any:
        """Intercepts tool output to parse <a2ui-json> and bypass the
        LLM summarization (avoiding sending many tokens of information
        that will not be processed).

        Args:
            tool: BaseTool executed.
            tool_args: Arguments passed.
            tool_context: ToolContext.
            result: Raw result.

        Returns:
            Sanitized or original result.
        """
        # Get the current session
        session_id = getattr(tool_context, "session_id", "default")

        # Get the text component of result (if any)
        text: str = self._get_result_text(result=result)

        a2ui_blocks = self._extract_a2ui_components(
            session_id=session_id,
            text=text
        )

        logger.info("after_tool_callback: session_id=%s, a2ui_blocks_found=%s", session_id, a2ui_blocks is not None)
        if a2ui_blocks is not None:
            # Tell ADK runner not to summarize the JSON component tree
            # tool_context.actions.skip_summarization = True
            return a2ui_blocks

        return result

    async def on_event_callback(
        self,
        *,
        invocation_context: InvocationContext,
        event: Event,
    ) -> Event | None:
        """Consolidates single or multiple A2UI cards into a unified multi-card surface."""
        session_id = getattr(invocation_context, "session_id", "default")
        
        # Guard: Only process and inject cards on the final response of the turn
        if not event.is_final_response():
            return event

        if not event.content or not event.content.parts:
            # Even if there is no event content generated yet, if we have pending cards, we must inject them
            if session_id in self._pending_cards and self._pending_cards[session_id]:
                event.content = types.Content(role="model", parts=[])
            else:
                return event

        extracted_card_payloads: list[list[dict[str, Any]]] = []

        # 1. Collect all A2UI payloads from event parts (if the agent generated any raw ones)
        for part in event.content.parts:
            text = self._extract_part_text(part)
            if not text:
                continue

            for match in re.finditer(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL):
                try:
                    ops = json.loads(match.group(1).strip())
                    if isinstance(ops, list):
                        extracted_card_payloads.append(ops)
                except Exception as err:
                    logger.error("Error parsing A2UI JSON in on_event_callback: %s", err)

        # 2. Append any pending cards stored during the tool execution in this session
        logger.info("on_event_callback: session_id=%s, pending_cards_count=%d", session_id, len(self._pending_cards.get(session_id, [])))
        if session_id in self._pending_cards:
            for card_str in self._pending_cards[session_id]:
                for match in re.finditer(r"<a2ui-json>(.*?)</a2ui-json>", card_str, re.DOTALL):
                    try:
                        ops = json.loads(match.group(1).strip())
                        if isinstance(ops, list):
                            extracted_card_payloads.append(ops)
                    except Exception as err:
                        logger.error("Error parsing stored A2UI JSON: %s", err)
            # Clear pending cards for this session after consuming them
            del self._pending_cards[session_id]

        # 3. Deduplicate identical card payloads
        logger.info("on_event_callback: unique card payloads count before deduplication=%d", len(extracted_card_payloads))
        unique_payloads: list[list[dict[str, Any]]] = []
        seen_surfaces: set[str] = set()

        for card_ops in extracted_card_payloads:
            surface_id = None
            for op in card_ops:
                if "beginRendering" in op:
                    surface_id = op["beginRendering"].get("surfaceId")
                    break
                if "surfaceUpdate" in op:
                    surface_id = op["surfaceUpdate"].get("surfaceId")
                    break
            if surface_id:
                if surface_id in seen_surfaces:
                    continue
                seen_surfaces.add(surface_id)
            unique_payloads.append(card_ops)

        extracted_card_payloads = unique_payloads

        if not extracted_card_payloads:
            return event

        # 4. Strip raw unmerged <a2ui-json> tags from event parts
        for part in event.content.parts:
            if hasattr(part, "text") and part.text:
                part.text = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", part.text, flags=re.DOTALL).strip()
            elif hasattr(part, "function_response") and part.function_response:
                resp = getattr(part.function_response, "response", None)
                if isinstance(resp, dict) and "result" in resp and isinstance(resp["result"], str):
                    resp["result"] = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", resp["result"], flags=re.DOTALL).strip()

        # 5. Merge all cards into a single Column container or handle single card case
        if len(extracted_card_payloads) == 1:
            card_ops = extracted_card_payloads[0]
            merged_str = f"<a2ui-json>\n{json.dumps(card_ops, indent=2)}\n</a2ui-json>"
            event.content.parts.append(types.Part.from_text(text=merged_str))
            return event

        # Multi-Card Case: Merge all cards into a single Column container with scoped component IDs
        unified_components: list[dict[str, Any]] = []
        card_root_ids: list[str] = []

        for idx, card_ops in enumerate(extracted_card_payloads):
            prefix = f"card_{idx}_"
            for op in card_ops:
                if "surfaceUpdate" in op:
                    components = op["surfaceUpdate"].get("components", [])
                    if not components:
                        continue

                    # Serialize to JSON string for efficient component ID remapping
                    comp_str = json.dumps(components)
                    orig_ids = [c["id"] for c in components if "id" in c]
                    orig_ids.sort(key=len, reverse=True)

                    # Prefix all component ID definitions and child references
                    for orig_id in orig_ids:
                        comp_str = comp_str.replace(f'"{orig_id}"', f'"{prefix}{orig_id}"')

                    prefixed_comps = json.loads(comp_str)
                    card_root_id = f"{prefix}card-root"
                    card_root_ids.append(card_root_id)
                    unified_components.extend(prefixed_comps)

        # Insert the parent Column layout holding all card roots
        unified_components.insert(
            0,
            {
                "id": "multi-card-root",
                "component": {
                    "Column": {
                        "children": {
                            "explicitList": card_root_ids
                        }
                    }
                }
            }
        )

        # Build the unified single-surface A2UI operation payload
        unified_payload = [
            {
                "version": "v0.8",
                "beginRendering": {
                    "surfaceId": "unified-system-cards",
                    "root": "multi-card-root"
                }
            },
            {
                "version": "v0.8",
                "surfaceUpdate": {
                    "surfaceId": "unified-system-cards",
                    "components": unified_components
                }
            }
        ]

        merged_str = f"<a2ui-json>\n{json.dumps(unified_payload, indent=2)}\n</a2ui-json>"
        event.content.parts.append(types.Part.from_text(text=merged_str))
        return event


    def _extract_a2ui_components(
        self,
        session_id: str,
        text: str
    ) -> Optional[str]:
        if "<a2ui-json>" in text:
            # Find and extract the A2UI blocks to store them in pending queue
            matches = re.findall(r"(<a2ui-json>.*?</a2ui-json>)", text, re.DOTALL)
            if matches:
                if session_id not in self._pending_cards:
                    self._pending_cards[session_id] = []
                self._pending_cards[session_id].extend(matches)
                
                # Strip the A2UI blocks from the text to return ONLY the plain text summary to the LLM
                clean_text = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", text, flags=re.DOTALL).strip()
                return clean_text
        return None

    @staticmethod
    def _get_result_text(result: Any) -> Optional[dict]:
        """
        Get the result dict with content that can be processed if the
        result passes the check gates: 1, the result is a dict; 2, the
        result contains content; 3, the content is a list of length > 0.
        If the result does not pass the check gates, return the result
        as a text string.

        Args:
            result: Any

        Returns:
            str: The result as a text string.
        """
        is_dict = isinstance(result, dict)
        has_content = result.get("content", {}) if is_dict else None
        content_is_list = isinstance(has_content, list)
        pass_gate = (
            is_dict
            and has_content
            and content_is_list
            and len(has_content)
        )

        if pass_gate:
            first_item = has_content[0]
            if isinstance(first_item, dict):
                return first_item.get("text", "")
            else:
                return str(first_item)

        return str(result)

    @staticmethod
    def _extract_part_text(part: Any) -> str:
        if hasattr(part, "text") and part.text:
            return part.text
        if hasattr(part, "function_response") and part.function_response:
            resp = getattr(part.function_response, "response", None)
            if isinstance(resp, str):
                return resp
            elif isinstance(resp, dict):
                if "result" in resp and isinstance(resp["result"], str):
                    return resp["result"]
                if "content" in resp and isinstance(resp["content"], list):
                    texts = []
                    for item in resp["content"]:
                        if isinstance(item, dict) and "text" in item:
                            texts.append(str(item["text"]))
                    if texts:
                        return "\n".join(texts)
                return json.dumps(resp)
        return ""
