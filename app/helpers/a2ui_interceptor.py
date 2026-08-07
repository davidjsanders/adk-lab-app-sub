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

"""A2UI Converter Interceptor for translating string payloads into native A2UI DataParts."""

import json
import logging
import re
from typing import Any

from a2a.types import (
    DataPart,
    Part,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
)
from google.adk.a2a.executor.config import ExecuteInterceptor

logger = logging.getLogger(__name__)


async def _a2ui_after_event(
    ctx: Any,
    a2a_event: Any,
    adk_event: Any,
) -> Any:
    """Interceptor hook that converts <a2ui-json> string payloads into DataParts with application/json+a2ui mimeType."""
    parts = []

    if isinstance(a2a_event, TaskStatusUpdateEvent) and a2a_event.status and a2a_event.status.message:
        parts = a2a_event.status.message.parts
    elif isinstance(a2a_event, TaskArtifactUpdateEvent) and a2a_event.artifact:
        parts = a2a_event.artifact.parts

    if not parts:
        return a2a_event

    new_parts = []
    for part in parts:
        part_root = getattr(part, "root", part)
        if isinstance(part_root, TextPart) and part_root.text:
            text = part_root.text
            if "<a2ui-json>" in text and "</a2ui-json>" in text:
                match = re.search(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                    try:
                        parsed_json = json.loads(json_str)
                        if isinstance(parsed_json, list):
                            for msg in parsed_json:
                                a2ui_part = Part(
                                    root=DataPart(
                                        data=msg,
                                        metadata={"mimeType": "application/json+a2ui"},
                                    )
                                )
                                new_parts.append(a2ui_part)
                        else:
                            a2ui_part = Part(
                                root=DataPart(
                                    data=parsed_json,
                                    metadata={"mimeType": "application/json+a2ui"},
                                )
                            )
                            new_parts.append(a2ui_part)
                        continue
                    except Exception as exc:
                        logger.error(f"Error parsing <a2ui-json> in interceptor: {exc}")
        new_parts.append(part)

    if isinstance(a2a_event, TaskStatusUpdateEvent) and a2a_event.status and a2a_event.status.message:
        a2a_event.status.message.parts = new_parts
    elif isinstance(a2a_event, TaskArtifactUpdateEvent) and a2a_event.artifact:
        a2a_event.artifact.parts = new_parts

    return a2a_event


a2ui_converter_interceptor = ExecuteInterceptor(after_event=_a2ui_after_event)
