import logging
import os
import re
from functools import cached_property
from typing import AsyncGenerator, override
from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import Client
from google.genai import types as genai_types

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GlobalGemini(Gemini):
    """Gemini model subclass enforcing global location endpoint routing to prevent regional 404s."""

    @override
    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool
    ) -> AsyncGenerator[LlmResponse, None]:
        """Intercepts the model request to strip A2UI JSON components from history to save context and latency."""
        logger.debug("generate_content_async intercepting request")
        if llm_request.contents:
            logger.debug("Found content, processing")
            for content in llm_request.contents:
                if content.parts:
                    logger.debug("Found parts, processing")
                    for part in content.parts:
                        logger.debug("Found part")
                        if isinstance(part.text, str) and "<a2ui-json>" in part.text:
                            logger.info("Part is A2UI, stripping JSON payload from conversation history")
                            part.text = re.sub(
                                r"<a2ui-json>.*?</a2ui-json>",
                                "",
                                part.text,
                                flags=re.DOTALL
                            ).strip()

        async for response in super().generate_content_async(llm_request, stream=stream):
            yield response

    @staticmethod
    def is_vertex(model: str) -> bool:
        """Determines if the model uses Vertex AI.

        Args:
            model: Model name string.

        Returns:
            Boolean indicating whether Vertex AI is enabled.
        """
        return (
            model.startswith("projects/")
            or os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "True"
        )

    @cached_property
    def api_client(self) -> Client:
        """Creates a Google GenAI API client configured with location='global'.

        Returns:
            Configured GenAI Client instance.
        """
        logger.debug("GlobalGemini api_client initialized for model: %s", self.model)
        base_url, api_version = self._base_url_and_api_version

        kwargs_for_http_options = {
            "headers": self._tracking_headers(),
            "retry_options": self.retry_options,
            "base_url": base_url,
        }

        if api_version:
            kwargs_for_http_options["api_version"] = api_version

        kwargs = {
            "http_options": genai_types.HttpOptions(**kwargs_for_http_options),
            "location": "global",
        }

        if self.is_vertex(self.model):
            kwargs["vertexai"] = True

        return Client(**kwargs)
