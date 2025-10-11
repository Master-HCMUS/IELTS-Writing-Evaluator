"""
Prompt Generator - Uses LLM to generate and refine prompts.

This module uses an LLM to iteratively improve prompts based on
performance feedback and error analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """A version of a prompt with metadata."""
    version_id: str
    system_prompt: str
    user_prompt_template: str
    generation_reasoning: str
    parent_version: Optional[str] = None


class PromptGenerator:
    """
    Generates and refines prompts using LLM feedback.
    
    This class uses an LLM to create new prompt variations based on
    performance feedback and error analysis.
    """
    
    def __init__(self, llm_client: Any):
        """
        Initialize the generator.
        
        Args:
            llm_client: LLM client for generating prompts
        """
        self.llm_client = llm_client
        self.prompt_history: List[PromptVersion] = []
    
    def _complete_text(self, prompt: str) -> str:
        """
        Get text completion from LLM for meta-prompting.
        
        Args:
            prompt: The meta-prompt to send
            
        Returns:
            Generated text response
        """
        if self.llm_client.mock_mode:
            # Return a simple default prompt in mock mode
            return """You are an expert IELTS examiner. Score the following Task 2 essay on a 0-9 band scale.

Provide scores for:
- Task Response
- Coherence & Cohesion  
- Lexical Resource
- Grammatical Range & Accuracy

Extract specific evidence quotes and identify errors."""
        
        try:
            # Use the underlying OpenAI client directly for text completion
            # Higher temperature for more creative and diverse prompt generation
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.model_scorer,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,  # Higher temperature for more variation
                max_tokens=2500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Text completion failed: {e}")
            # Fallback to a reasonable default prompt
            return """You are an expert IELTS examiner. Score the following Task 2 essay on a 0-9 band scale.

Provide scores for:
- Task Response
- Coherence & Cohesion
- Lexical Resource
- Grammatical Range & Accuracy

Extract specific evidence quotes and identify errors."""
    
    def generate_initial_prompt(
        self,
        rubric_summary: str,
        example_essays: List[Dict[str, Any]],
        base_prompt: str = None
    ) -> PromptVersion:
        """
        Generate an initial prompt based on rubric and examples.
        
        Args:
            rubric_summary: Summary of IELTS rubric
            example_essays: List of example essays with scores
            base_prompt: Optional base prompt to enhance (e.g., from task2.py)
            
        Returns:
            Initial PromptVersion
        """
        logger.info("Generating initial prompt...")
        
        # Format examples
        examples_text = "\n\n".join([
            f"Essay (Band {ex['overall']}):\n{ex['essay'][:500]}...\nQuestion: {ex.get('question', 'N/A')}"
            for ex in example_essays[:3]
        ])
        
        if base_prompt:
            # Enhance existing prompt
            meta_prompt = f"""You are an expert prompt engineer specializing in IELTS scoring systems.

TASK: Enhance the existing IELTS scoring prompt to improve accuracy while preserving its structure and format.

CURRENT BASE PROMPT:
```
{base_prompt}
```

RUBRIC SUMMARY:
{rubric_summary}

EXAMPLE ESSAYS (for calibration reference):
{examples_text}

CRITICAL REQUIREMENTS:
1. Output must be a PROSE TEXT PROMPT (not JSON, not structured data - just natural language instructions)
2. PRESERVE exactly as-is: all "CRITICAL INSTRUCTIONS" and "RESPONSE STRUCTURE IN JSON" sections
3. PRESERVE the overall format and tone of the base prompt
4. ADD new sections AFTER the existing rubric to enhance scoring guidance

ENHANCEMENT REQUIREMENTS (add these as new sections):
1. ADD "BAND DESCRIPTORS" section with detailed characteristics for Bands 4, 5, 6, 7, 8
   Example: "Band 7: Ideas are well-developed with relevant examples. 1-2 grammatical errors maximum."
2. ADD "ERROR CALIBRATION" section with specific thresholds
   Example: "1-2 major errors = Band 7, 3-5 errors = Band 6, 6+ errors = Band 5 or lower"
3. ADD "SCORING CALIBRATION" section with numerical anchors
   Example: "Band 6: Competent but with noticeable errors. Band 7: Good with occasional minor errors."
4. ADD "COMMON PITFALLS" section warning examiners about typical mistakes
   Example: "Avoid over-scoring based only on length. Avoid under-scoring for minor vocabulary issues."

TARGET: >75% of scores within 0.5 points of human expert scores

OUTPUT FORMAT:
Generate the complete enhanced prompt as PLAIN TEXT (like the input).
Start with the exact same opening lines as the base prompt.
Keep all existing sections intact.
Add new sections at appropriate places (after rubric, before RESPONSE STRUCTURE IN JSON).
The result should look like a natural extension of the base prompt."""
        else:
            # Generate from scratch
            meta_prompt = f"""You are an expert prompt engineer specializing in IELTS scoring systems.

Create a DETAILED and PRECISE system prompt for an LLM that will score IELTS Task 2 essays.

CRITICAL REQUIREMENTS:
1. Score essays on 0-9 band scale (0.5 increments allowed)
2. Cover FOUR criteria: Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy
3. TARGET: >75% of scores must be within 0.5 points of human expert scores
4. Extract specific evidence quotes from the essay (minimum 2-3 per criterion)
5. Identify concrete errors with examples from the text

RUBRIC SUMMARY:
{rubric_summary}

EXAMPLE ESSAYS:
{examples_text}

YOUR PROMPT MUST INCLUDE:
1. **Band Descriptors**: Clear descriptions of what Band 5, 6, 7, 8 essays look like
2. **Error Calibration**: Guidance on how many/what types of errors = which band
   Example: "Band 7: Max 1-2 grammatical errors; Band 6: 3-5 errors; Band 5: frequent errors"
3. **Common Pitfalls**: Warnings about over/under-scoring tendencies
4. **Scoring Process**: Step-by-step instructions (read → identify strengths → count errors → calibrate → score)
5. **Evidence Requirements**: Must quote specific phrases from essay to justify each score

STYLE:
- Be direct and prescriptive (use imperatives: "Count the errors", "Identify vocabulary range")
- Include 3-5 concrete examples of scoring decisions
- Add numerical anchors where possible
- Structure logically (criteria → process → calibration → output format)

Generate ONLY the comprehensive system prompt (300-500 words). Make it actionable and specific."""

        try:
            response = self._complete_text(meta_prompt)
            system_prompt = response.strip()
            
            # Strip markdown code blocks if present
            if system_prompt.startswith("```") and system_prompt.endswith("```"):
                lines = system_prompt.split("\n")
                # Remove first line (opening ```) and last line (closing ```)
                system_prompt = "\n".join(lines[1:-1]).strip()
            
            # Ensure RESPONSE STRUCTURE IN JSON is present (critical for evaluation)
            if "RESPONSE STRUCTURE IN JSON" not in system_prompt or "per_criterion" not in system_prompt:
                logger.warning("Generated prompt missing RESPONSE STRUCTURE IN JSON, adding it...")
                system_prompt += "\n\nRESPONSE STRUCTURE IN JSON:\n"
                system_prompt += "- per_criterion: array of criterion assessments\n"
                system_prompt += "  - name: criterion name\n"
                system_prompt += "  - band: numeric score (0-9, increments of 0.5)\n"
                system_prompt += "  - evidence_quotes: array of verbatim quotes (max 3)\n"
                system_prompt += "  - errors: array of error objects (max 10)\n"
                system_prompt += "    - span: exact problematic text\n"
                system_prompt += "    - type: \"grammar\" | \"lexical\" | \"coherence\" | \"task\" | \"other\"\n"
                system_prompt += "    - fix: brief correction\n"
                system_prompt += "  - suggestions: array of specific improvements (max 5, each ≤200 chars)\n"
                system_prompt += "- overall: overall band (0-9, increments of 0.5)\n"
            
            # Create user prompt template
            user_prompt_template = """Task 2 Question:
{question}

Score this IELTS Task 2 essay according to the rubric:

{essay}

Provide your assessment in the specified JSON format."""
            
            version = PromptVersion(
                version_id="v1_initial",
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                generation_reasoning="Initial prompt generated from rubric and examples"
            )
            
            self.prompt_history.append(version)
            logger.info(f"Generated initial prompt: {len(system_prompt)} characters")
            return version
            
        except Exception as e:
            logger.error(f"Failed to generate initial prompt: {e}")
            raise
    
    def refine_prompt_direct(
        self,
        current_prompt: PromptVersion,
        sample_essay: str,
        sample_question: str,
        true_score: float,
        predicted_score: float,
        error: float
    ) -> PromptVersion:
        """
        Generate an improved prompt designed to score the sample correctly.
        
        This gives the LLM flexibility to either enhance the current prompt or
        create a completely new one based on what will work best for the target score.
        
        Args:
            current_prompt: Current prompt version (can be used as foundation)
            sample_essay: The essay that needs correct scoring
            sample_question: The IELTS question
            true_score: Ground truth score (e.g., 9.0)
            predicted_score: What the current prompt produced (e.g., 6.5)
            error: Absolute error (e.g., 2.5)
            
        Returns:
            Improved PromptVersion designed to score this sample correctly
        """
        logger.info(f"Refining prompt to fit sample (current: {current_prompt.version_id})...")
        logger.info(f"  Target: {true_score}, Current got: {predicted_score}, Error: {error:.2f}")
        
        # Truncate essay for context
        essay_excerpt = sample_essay[:1000] + "..." if len(sample_essay) > 1000 else sample_essay
        
        # Determine scoring characteristics based on the target
        if true_score >= 7.5:
            scoring_hint = "This essay deserves a HIGH score (7.5-9.0). The prompt should recognize advanced writing quality, sophisticated vocabulary, complex grammar, and excellent task response."
        elif true_score >= 6.0:
            scoring_hint = "This essay deserves a COMPETENT score (6.0-7.0). The prompt should balance recognition of adequate skills with awareness of noticeable errors."
        else:
            scoring_hint = "This essay deserves a BELOW-AVERAGE score (below 6.0). The prompt should identify significant weaknesses in task response, coherence, vocabulary, or grammar."
        
        meta_prompt = f"""You are an expert IELTS prompt engineer. Your task is to create a scoring prompt that will correctly score the given essay.

CURRENT SCORING PROMPT:
```
{current_prompt.system_prompt}
```

TARGET ESSAY TO SCORE CORRECTLY:
Question: {sample_question}

Essay:
{essay_excerpt}

SCORING PROBLEM:
- GROUND TRUTH: This essay should score **{true_score}** overall
- CURRENT PROMPT SCORED IT: {predicted_score}
- ERROR: {error:.2f} points off

{scoring_hint}

YOUR TASK:
Create an improved scoring prompt that will correctly score THIS essay close to {true_score} (within 0.5 points).

YOU HAVE TWO OPTIONS - choose whichever you think will work best:

**OPTION 1: ENHANCE THE CURRENT PROMPT**
- Keep the overall structure and good parts of the current prompt
- Modify specific sections (band descriptors, calibration, examples) to fix the scoring error
- Add new guidance or adjust existing guidance to achieve the target score

**OPTION 2: CREATE A COMPLETELY NEW PROMPT**
- Start fresh with a new scoring philosophy and structure
- Design from scratch based on what will correctly score this essay
- Ignore the current prompt if you think a different approach is better

Choose the option that you believe will most effectively achieve a score of {true_score} for this essay.

MANDATORY REQUIREMENTS (apply to both options):
1. Must evaluate IELTS Task 2 essays on a 0-9 band scale (0.5 increments)
2. Must score FOUR criteria: Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy
3. MUST include this EXACT response structure at the end:

RESPONSE STRUCTURE:
- per_criterion: array of criterion assessments
  - name: criterion name
  - band: numeric score (0-9, increments of 0.5)
  - evidence_quotes: array of verbatim quotes (max 3)
  - errors: array of error objects (max 10)
    - span: exact problematic text
    - type: "grammar" | "lexical" | "coherence" | "task" | "other"
    - fix: brief correction
  - suggestions: array of specific improvements (max 5, each ≤200 chars)
- overall: overall band (0-9, increments of 0.5)

4. Must end with: "CRITICAL INSTRUCTIONS: Output ONLY valid JSON matching the structure above. No explanations, no markdown."

DESIGN CONSIDERATIONS:
- How lenient/strict should band descriptors be for a {true_score} essay?
- What error tolerance is appropriate?
- What qualities should be emphasized or de-emphasized?
- Would calibration examples help anchor the scoring?

OUTPUT FORMAT:
Generate the COMPLETE IMPROVED PROMPT as plain prose text (no meta-commentary, no markdown code blocks).
Start with something like "You are an expert IELTS examiner..." and end with the RESPONSE STRUCTURE and CRITICAL INSTRUCTIONS."""

        try:
            response = self._complete_text(meta_prompt)
            refined_prompt = response.strip()
            
            # Strip markdown code blocks if present
            if refined_prompt.startswith("```") and refined_prompt.endswith("```"):
                lines = refined_prompt.split("\n")
                refined_prompt = "\n".join(lines[1:-1]).strip()
            
            # Ensure RESPONSE STRUCTURE is present
            if "RESPONSE STRUCTURE" not in refined_prompt or "per_criterion" not in refined_prompt:
                logger.warning("Refined prompt missing RESPONSE STRUCTURE, adding it...")
                refined_prompt += "\n\nRESPONSE STRUCTURE:\n"
                refined_prompt += "- per_criterion: array of criterion assessments\n"
                refined_prompt += "  - name: criterion name\n"
                refined_prompt += "  - band: numeric score (0-9, increments of 0.5)\n"
                refined_prompt += "  - evidence_quotes: array of verbatim quotes (max 3)\n"
                refined_prompt += "  - errors: array of error objects (max 10)\n"
                refined_prompt += "    - span: exact problematic text\n"
                refined_prompt += "    - type: \"grammar\" | \"lexical\" | \"coherence\" | \"task\" | \"other\"\n"
                refined_prompt += "    - fix: brief correction\n"
                refined_prompt += "  - suggestions: array of specific improvements (max 5, each ≤200 chars)\n"
                refined_prompt += "- overall: overall band (0-9, increments of 0.5)\n"
            
            # Increment version
            version_num = int(current_prompt.version_id.split('_')[0][1:]) + 1
            
            version = PromptVersion(
                version_id=f"v{version_num}_direct_refined",
                system_prompt=refined_prompt,
                user_prompt_template=current_prompt.user_prompt_template,
                generation_reasoning=f"Direct refinement from {current_prompt.version_id}. "
                                   f"Target: {true_score}, Was: {predicted_score}, Error: {error:.2f}",
                parent_version=current_prompt.version_id
            )
            
            self.prompt_history.append(version)
            logger.info(f"Generated refined prompt: {version.version_id}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to refine prompt: {e}")
            raise
    

    def save_prompt_history(self, filepath: str) -> None:
        """Save prompt generation history to file."""
        import json
        from pathlib import Path
        
        history_data = [
            {
                "version_id": p.version_id,
                "system_prompt": p.system_prompt,
                "user_prompt_template": p.user_prompt_template,
                "generation_reasoning": p.generation_reasoning,
                "parent_version": p.parent_version
            }
            for p in self.prompt_history
        ]
        
        Path(filepath).write_text(
            json.dumps(history_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info(f"Saved {len(history_data)} prompt versions to {filepath}")
