from __future__ import annotations

import json
import logging
from typing import Any

from openai import AzureOpenAI

from ..config import settings
from ..versioning.determinism import TEMPERATURE, TOP_P
from .task2_stub import score_once_task2

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper for Azure OpenAI with mock fallback for local testing."""
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode or not settings.azure_openai_api_key
        
        if self.mock_mode:
            logger.info("LLM client in MOCK mode (no Azure credentials)")
            self.client = None
        else:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
    
    def score_task2(self, system_prompt: str, user_prompt: str, schema: dict) -> tuple[dict[str, Any], dict[str, int]]:
        """
        Score Task 2 essay using LLM or mock.
        Returns (response_json, token_usage).
        """
        if self.mock_mode:
            # Use deterministic stub for local testing
            essay = user_prompt.split("essay according to the rubric:\n\n")[-1]
            essay = essay.split("\n\nProvide your assessment")[0]
            mock_response = score_once_task2(essay)
            token_usage = {
                "input_tokens": len(system_prompt.split()) + len(user_prompt.split()),
                "output_tokens": 100,
            }
            return mock_response, token_usage
        
        try:
            response = self.client.chat.completions.create(
                model=settings.azure_openai_deployment_scorer,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
                response_format={"type": "json_object"},
                max_tokens=1500,
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            token_usage = {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            }
            
            return parsed, token_usage
            
        except Exception as e:
            logger.error(f"LLM scoring failed: {e}")
            # Fallback to stub on error
            essay = user_prompt.split("essay according to the rubric:\n\n")[-1]
            essay = essay.split("\n\nProvide your assessment")[0]
            return score_once_task2(essay), {"input_tokens": 0, "output_tokens": 0}
