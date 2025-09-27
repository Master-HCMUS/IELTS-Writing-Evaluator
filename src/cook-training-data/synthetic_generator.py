from __future__ import annotations

import json
import asyncio
import re
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI
from src.app.config import settings


class SyntheticDataGenerator:
    """
    Generate synthetic evidence_quotes, errors, and suggestions using Azure OpenAI.
    """
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode or not settings.azure_openai_api_key
        
        if not self.mock_mode:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
    
    def _extract_quotes_from_essay(self, essay: str, criterion: str, max_quotes: int = 3) -> List[str]:
        """
        Extract relevant quotes from essay based on criterion.
        """
        sentences = re.split(r'[.!?]+', essay)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) <= max_quotes:
            return sentences[:max_quotes]
        
        # Simple heuristic: take sentences from different parts of the essay
        indices = [0, len(sentences)//2, len(sentences)-1]
        return [sentences[i] for i in indices if i < len(sentences)][:max_quotes]
    
    def _generate_mock_errors(self, essay: str, criterion: str) -> List[Dict[str, str]]:
        """
        Generate mock errors for testing.
        """
        sentences = re.split(r'[.!?]+', essay)
        if not sentences:
            return []
        
        error_types = {
            "Task Response": "task",
            "Coherence & Cohesion": "coherence", 
            "Lexical Resource": "lexical",
            "Grammatical Range & Accuracy": "grammar"
        }
        
        error_type = error_types.get(criterion, "other")
        
        # Take first sentence with some words
        sentence = next((s.strip() for s in sentences if len(s.strip()) > 20), "")
        if not sentence:
            return []
        
        # Create a mock error
        span = sentence[:100]  # First 100 chars
        fix = f"Consider improving the {criterion.lower()} aspect here."
        
        return [{
            "span": span,
            "type": error_type,
            "fix": fix
        }]
    
    def _generate_mock_suggestions(self, criterion: str) -> List[str]:
        """
        Generate mock suggestions based on criterion.
        """
        suggestions_map = {
            "Task Response": [
                "Develop your main arguments more fully with specific examples.",
                "Ensure you address all parts of the question directly."
            ],
            "Coherence & Cohesion": [
                "Use more varied linking words to connect your ideas.",
                "Improve paragraph structure with clearer topic sentences."
            ],
            "Lexical Resource": [
                "Use more sophisticated vocabulary and avoid repetition.",
                "Focus on precise word choice and natural collocations."
            ],
            "Grammatical Range & Accuracy": [
                "Use more complex sentence structures.",
                "Check for grammatical errors and improve accuracy."
            ]
        }
        
        return suggestions_map.get(criterion, ["Improve this criterion further."])
    
    async def generate_synthetic_data(self, essay: str, criterion: str, band: float) -> Dict[str, Any]:
        """
        Generate synthetic evidence_quotes, errors, and suggestions for a criterion.
        
        Args:
            essay: The essay text
            criterion: The criterion name
            band: The band score for this criterion
            
        Returns:
            Dictionary with evidence_quotes, errors, suggestions
        """
        if self.mock_mode:
            return {
                "evidence_quotes": self._extract_quotes_from_essay(essay, criterion),
                "errors": self._generate_mock_errors(essay, criterion),
                "suggestions": self._generate_mock_suggestions(criterion)
            }
        
        # Generate using Azure OpenAI
        system_prompt = f"""You are an IELTS examiner analyzing essays for {criterion}.

Your task:
1. Extract 1-3 direct verbatim quotes from the essay that demonstrate the {criterion} performance
2. Identify 0-3 specific errors related to {criterion}
3. Provide 1-3 specific improvement suggestions

The band score for {criterion} is {band}.

Respond in JSON format:
{{
  "evidence_quotes": ["quote1", "quote2"],
  "errors": [
    {{"span": "exact text from essay", "type": "appropriate_type", "fix": "specific correction"}}
  ],
  "suggestions": ["specific suggestion 1", "specific suggestion 2"]
}}

Ensure all quotes and error spans are EXACTLY from the essay text."""

        user_prompt = f"""Essay to analyze:

{essay}

Analyze for {criterion} (band {band}) and provide the JSON response."""

        try:
            response = self.client.chat.completions.create(
                model=settings.azure_openai_deployment_scorer,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Validate and clean the result
            result["evidence_quotes"] = result.get("evidence_quotes", [])[:3]
            result["errors"] = result.get("errors", [])[:10]
            result["suggestions"] = result.get("suggestions", [])[:5]
            
            return result
            
        except Exception as e:
            print(f"Error generating synthetic data for {criterion}: {e}")
            # Fallback to mock data
            return {
                "evidence_quotes": self._extract_quotes_from_essay(essay, criterion),
                "errors": self._generate_mock_errors(essay, criterion),
                "suggestions": self._generate_mock_suggestions(criterion)
            }
    
    async def enhance_per_criterion(self, per_criterion: List[Dict[str, Any]], essay: str) -> List[Dict[str, Any]]:
        """
        Enhance per_criterion data with synthetic evidence_quotes, errors, suggestions.
        
        Args:
            per_criterion: List of criterion dictionaries
            essay: The essay text
            
        Returns:
            Enhanced per_criterion list
        """
        enhanced = []
        
        for criterion_data in per_criterion:
            criterion_name = criterion_data.get("name", "")
            band = criterion_data.get("band", 5.0)
            
            # Generate synthetic data
            synthetic = await self.generate_synthetic_data(essay, criterion_name, band)
            
            # Update the criterion data
            enhanced_criterion = criterion_data.copy()
            enhanced_criterion.update({
                "evidence_quotes": synthetic["evidence_quotes"],
                "errors": synthetic["errors"],
                "suggestions": synthetic["suggestions"]
            })
            
            enhanced.append(enhanced_criterion)
        
        return enhanced