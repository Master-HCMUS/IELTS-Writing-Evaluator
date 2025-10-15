from __future__ import annotations

import time
from typing import Any

from ..config import settings
from ..prompts.question_generator import (
    generate_question_id,
    get_response_schema,
    get_system_prompt,
    get_user_prompt
)
from ..scoring.llm_client import LLMClient
from ..validation.schemas import validate_generate_question_response


def generate_question(difficulty: str = "medium", topic: str | None = None, llm_client: LLMClient | None = None) -> dict[str, Any]:
    """Generate an IELTS Task 2 question using OpenAI.

    Args:
        difficulty: Difficulty level ("easy", "medium", "hard")
        topic: Optional specific topic
        llm_client: Optional LLM client instance

    Returns:
        Dict containing question data with id, question, topic, and difficulty
    """
    llm = llm_client or LLMClient()

    system_prompt = get_system_prompt()
    user_prompt = get_user_prompt(difficulty=difficulty, topic=topic)
    schema = get_response_schema()

    start = time.perf_counter()

    # Generate the question using LLM
    response_json, tokens = llm.generate_question(system_prompt, user_prompt, schema)

    # Add unique ID first
    question_data = response_json.copy()
    question_data["id"] = generate_question_id()

    # Validate the response
    try:
        validate_generate_question_response(question_data)
    except Exception as e:
        # If validation fails, return a fallback question
        print(f"Question generation validation failed: {e}")
        question_data = _get_fallback_question(difficulty, topic)
        question_data["id"] = generate_question_id()

    return question_data


def _get_fallback_question(difficulty: str, topic: str | None = None) -> dict[str, Any]:
    """Fallback questions in case of generation failure."""
    fallback_questions = {
        "easy": {
            "question": "Some people believe that children should be allowed to stay at home and play until they are six or seven years old. Others believe that it is important for young children to go to school as soon as possible. Discuss both views and give your own opinion.",
            "topic": "Education",
            "difficulty": "easy"
        },
        "medium": {
            "question": "Some people believe that technology has made our lives more complex. Others think it has made life easier. Discuss both views and give your own opinion.",
            "topic": "Technology",
            "difficulty": "medium"
        },
        "hard": {
            "question": "Some people think that universities should provide graduates with the knowledge and skills needed in the workplace. Others think that the true function of a university should be to give access to knowledge for its own sake. Discuss both views and give your own opinion.",
            "topic": "Education",
            "difficulty": "hard"
        }
    }

    # Try to match topic if provided, otherwise use difficulty-based fallback
    if topic and difficulty == "medium":
        topic_questions = {
            "Technology": "Many people believe that social networking sites have a negative impact on individuals and society. To what extent do you agree or disagree?",
            "Education": "In many countries, the proportion of older people is steadily increasing. Does this trend have more positive or negative effects on society?",
            "Society": "Some people think that the best way to reduce crime is to give longer prison sentences. Others, however, believe there are better alternative ways of reducing crime. Discuss both views and give your opinion.",
        }
        if topic.title() in topic_questions:
            return {
                "question": topic_questions[topic.title()],
                "topic": topic.title(),
                "difficulty": difficulty
            }

    return fallback_questions.get(difficulty, fallback_questions["medium"])
