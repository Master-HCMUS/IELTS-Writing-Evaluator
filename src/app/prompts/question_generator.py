from __future__ import annotations

import json
from pathlib import Path
import ulid


def get_system_prompt() -> str:
    """System prompt for generating IELTS Task 2 questions."""
    return """You are an experienced IELTS question writer creating authentic Task 2 essay questions.

CRITICAL INSTRUCTIONS:
1. Respond ONLY in valid JSON format. No explanatory text outside JSON.
2. Create questions that follow IELTS Task 2 format: discussion, opinion, advantage/disadvantage, problem/solution, or two-part questions.
3. Questions should be suitable for academic writing assessment.
4. Include both sides of the argument for discussion-type questions.
5. Keep questions between 30-80 words.
6. Use formal, academic language.

QUESTION TYPES:
- Discussion: "Some people think X. Others think Y. Discuss both views and give your own opinion."
- Opinion: "To what extent do you agree or disagree with the following statement?"
- Advantage/Disadvantage: "What are the advantages and disadvantages of X?"
- Problem/Solution: "What are the problems associated with X and what solutions can you suggest?"
- Two-part: "Why is X important? How can Y be improved?"

TOPICS: Technology, Education, Environment, Health, Society, Economy, Culture, Work, Family, Government, Crime, Media, Transport, Sports, Food, Travel, Science, Arts.

DIFFICULTY LEVELS:
- Easy: Straightforward topics, clear arguments, common vocabulary
- Medium: Balanced complexity, some abstract concepts, varied vocabulary
- Hard: Complex topics, nuanced arguments, sophisticated vocabulary and structures

RESPONSE FORMAT:
Return a JSON object with exactly these fields:
- question: The complete IELTS Task 2 question text
- topic: Main topic category (one word)
- difficulty: "easy", "medium", or "hard" """


def get_user_prompt(difficulty: str = "medium", topic: str | None = None) -> str:
    """User prompt for generating a question with specific parameters."""
    prompt = f"Generate an IELTS Task 2 question with {difficulty} difficulty level."

    if topic:
        prompt += f" The topic should be related to {topic}."

    prompt += "\n\nProvide your response in the specified JSON format."

    return prompt


def get_response_schema() -> dict:
    """Schema hint for the question generation model."""
    return {
        "type": "object",
        "properties": {
            "question": {"type": "string", "minLength": 30, "maxLength": 200},
            "topic": {"type": "string", "minLength": 1, "maxLength": 50},
            "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]}
        },
        "required": ["question", "topic", "difficulty"]
    }


def generate_question_id() -> str:
    """Generate a unique ID for a question."""
    return str(ulid.new())
