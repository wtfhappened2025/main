import os
import json
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert explainer.

Your task is to explain complex news, technology, finance, science,
and internet topics in simple language.

Rules:
- Write for a 15-year-old audience.
- Use clear cause-and-effect explanations.
- Keep explanations concise.
- Avoid political bias or speculation.
- Prefer factual reasoning.
- Maximum 50 words per explanation card.

All explanations must follow this structure:

Card 1 – What Happened
Card 2 – Why It Happened
Card 3 – Why It Matters

You MUST respond in valid JSON format only. No markdown, no code blocks, no extra text."""


EXPLANATION_PROMPT = """Convert the following topic into three explanation cards.

Topic: {topic}

Respond ONLY with this exact JSON structure, no other text:
{{
  "normalized_question": "A clear question form of the topic",
  "card_1": "What happened - explain the event simply (max 50 words)",
  "card_2": "Why it happened - explain the cause (max 50 words)",  
  "card_3": "Why it matters - explain the impact (max 50 words)",
  "card_1_detail": "Additional context for card 1 (1-2 sentences)",
  "card_2_detail": "Additional context for card 2 (1-2 sentences)",
  "card_3_detail": "Additional context for card 3 (1-2 sentences)",
  "category": "one of: technology, finance, world_news, science, internet_culture, politics, economy, ai, crypto"
}}"""


CAPTION_PROMPT = """Generate a short, engaging social media caption for this topic explanation.

Topic: {topic}
Card 1: {card_1}
Card 2: {card_2}
Card 3: {card_3}

Respond ONLY with a JSON object:
{{
  "caption": "A short engaging caption with an emoji, under 100 characters",
  "hashtags": ["tag1", "tag2", "tag3"]
}}"""


async def generate_explanation(topic: str) -> dict:
    """Generate 3-card explanation for a topic using Claude."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not set")

    import uuid
    chat = LlmChat(
        api_key=api_key,
        session_id=f"explain-{uuid.uuid4().hex[:8]}",
        system_message=SYSTEM_PROMPT
    )
    chat.with_model("anthropic", "claude-sonnet-4-5-20250929")

    prompt = EXPLANATION_PROMPT.format(topic=topic)
    user_msg = UserMessage(text=prompt)

    try:
        response = await chat.send_message(user_msg)
        # Parse JSON from response
        response_text = response.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}, raw: {response}")
        raise ValueError(f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        raise


async def generate_caption(topic: str, card_1: str, card_2: str, card_3: str) -> dict:
    """Generate social media caption for an explanation."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not set")

    import uuid
    chat = LlmChat(
        api_key=api_key,
        session_id=f"caption-{uuid.uuid4().hex[:8]}",
        system_message="You are a social media expert. Respond only in valid JSON."
    )
    chat.with_model("anthropic", "claude-sonnet-4-5-20250929")

    prompt = CAPTION_PROMPT.format(topic=topic, card_1=card_1, card_2=card_2, card_3=card_3)
    user_msg = UserMessage(text=prompt)

    try:
        response = await chat.send_message(user_msg)
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Caption generation failed: {e}")
        return {"caption": f"{topic}", "hashtags": ["trending", "explained"]}
