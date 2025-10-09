from __future__ import annotations

import json
import logging
from typing import Any

from openai import AzureOpenAI, OpenAI

from ..config import settings
from ..versioning.determinism import TEMPERATURE, TOP_P
from .task2_stub import score_once_task2

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper for multiple OpenAI API providers with mock fallback for local testing."""

    def __init__(self, mock_mode: bool = False, provider: str | None = None):
        # Use provided provider or fall back to settings
        self.provider = provider or settings.api_provider
        self.mock_mode = mock_mode

        # Determine if we're in mock mode based on provider availability
        if self.provider == "azure":
            self.mock_mode = self.mock_mode or not settings.azure_openai_api_key
        elif self.provider == "openai":
            self.mock_mode = self.mock_mode or not settings.openai_api_key
        else:
            logger.warning(f"Unknown provider '{self.provider}', falling back to mock mode")
            self.mock_mode = True

        if self.mock_mode:
            logger.info(f"LLM client in MOCK mode (provider: {self.provider})")
            self.client = None
        else:
            if self.provider == "azure":
                self.client = AzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_version=settings.azure_openai_api_version,
                )
                self.model_scorer = settings.azure_openai_deployment_scorer
            elif self.provider == "openai":
                # Unified OpenAI-compatible client (works with OpenAI direct API and other providers)
                client_kwargs = {"api_key": settings.openai_api_key}
                if settings.openai_base_url:
                    client_kwargs["base_url"] = settings.openai_base_url
                self.client = OpenAI(**client_kwargs)
                self.model_scorer = settings.openai_model_scorer
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
    
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
                model=self.model_scorer,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
                response_format={"type": "json_object"},
                max_tokens=3000,
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            token_usage = {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            }
            
            return parsed, token_usage
            
        except Exception as e:
            logger.error(f"Task 2 scoring failed: {e}")
            # Fallback to stub on error
            essay = user_prompt.split("essay according to the rubric:\n\n")[-1]
            essay = essay.split("\n\nProvide your assessment")[0]
            return score_once_task2(essay), {"input_tokens": 0, "output_tokens": 0}

    def score_rubric(self, system_prompt: str, user_prompt: str, schema: dict) -> tuple[dict[str, Any], dict[str, int]]:
        """
        Score a single rubric criterion using LLM or mock.
        Returns (response_json, token_usage).
        """
        if self.mock_mode:
            # Use deterministic stub for local testing
            from .rubric_stub import score_single_rubric_mock
            essay = user_prompt.split("essay for")[0].split(":\n\n")[-1]
            if "\n\nProvide your" in essay:
                essay = essay.split("\n\nProvide your")[0]
            mock_response = score_single_rubric_mock(essay, system_prompt)
            token_usage = {
                "input_tokens": len(system_prompt.split()) + len(user_prompt.split()),
                "output_tokens": 50,
            }
            return mock_response, token_usage
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_scorer,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
                response_format={"type": "json_object"},
                max_tokens=5500,  # Smaller for single rubric
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            token_usage = {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            }
            
            return parsed, token_usage
            
        except Exception as e:
            logger.error(f"Rubric scoring failed: {e}")
            # Fallback to stub on error
            from .rubric_stub import score_single_rubric_mock
            essay = user_prompt.split("essay for")[0].split(":\n\n")[-1]
            if "\n\nProvide your" in essay:
                essay = essay.split("\n\nProvide your")[0]
            return score_single_rubric_mock(essay, system_prompt), {"input_tokens": 0, "output_tokens": 0}