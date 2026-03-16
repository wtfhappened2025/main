import os
import json
import logging
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# ─── Default Prompts (seeded into DB, editable via admin) ───

PROMPT_1_SYSTEM = """You are a news analyst. Extract the key facts from news content and structure them clearly. Focus only on information supported by the input. Do not speculate."""

PROMPT_1_TASK = """Analyze the following topic and extract structured facts.

Topic: {topic}

Identify:
1. The core event
2. Key actors
3. Main causes
4. Immediate outcomes
5. Broader implications

Respond ONLY with this exact JSON structure, no other text:
{{
  "event": "Clear description of the core event",
  "actors": ["actor1", "actor2"],
  "causes": ["cause1", "cause2"],
  "outcomes": ["outcome1", "outcome2"],
  "implications": ["implication1", "implication2"],
  "category": "one of: technology, finance, world_news, science, internet_culture, politics, economy, ai, crypto"
}}"""

PROMPT_2_SYSTEM = """You are an analyst identifying the underlying drivers behind news events. Analyze the structured facts and determine the real forces causing the event. Focus on:
- economic drivers
- technological shifts
- political pressures
- market forces
- global trends"""

PROMPT_2_TASK = """Given these structured facts about a news event, identify the deeper structural forces behind it.

Event: {event}
Actors: {actors}
Causes: {causes}
Outcomes: {outcomes}
Implications: {implications}

Respond ONLY with this exact JSON structure, no other text:
{{
  "primary_drivers": ["driver1", "driver2"],
  "secondary_drivers": ["driver1", "driver2"],
  "trend_type": "one of: technology_shift, economic_pressure, policy_change, geopolitical_event, market_reaction"
}}"""

PROMPT_3_SYSTEM = """You are an expert explainer for the WTFHappened app. Generate three short explanation cards that help users understand:
1. What happened
2. Why it happened
3. Why it matters to them — split into "How it affects me" and "What should I do"

Rules:
- Each card must contain 3-4 bullet points
- Each bullet must be under 15 words
- Use simple language
- Avoid jargon
- Focus on clarity and usefulness
- Card 3 MUST be split into two sections: "affects" (how this impacts the reader personally) and "action" (concrete steps the reader can take). Use "you" and "your" to address the reader directly."""

PROMPT_3_TASK = """Transform this analysis into three user-facing explanation cards.

Event: {event}
Actors: {actors}
Outcomes: {outcomes}
Primary Drivers: {primary_drivers}
Secondary Drivers: {secondary_drivers}
Implications: {implications}

Respond ONLY with this exact JSON structure, no other text:
{{
  "normalized_question": "A clear question form of the topic",
  "card_1_title": "What Happened",
  "card_1_points": ["point1", "point2", "point3"],
  "card_2_title": "Why It Happened",
  "card_2_points": ["point1", "point2", "point3"],
  "card_3_affects": ["How this affects you point1", "How this affects you point2", "How this affects you point3"],
  "card_3_action": ["What you should do point1", "What you should do point2", "What you should do point3"],
  "category": "one of: technology, finance, world_news, science, internet_culture, politics, economy, ai, crypto"
}}"""

CAPTION_SYSTEM = """You are a social media expert. Respond only in valid JSON."""

CAPTION_TASK = """Generate a short, engaging social media caption for this topic explanation.

Topic: {topic}
Card 1: {card_1}
Card 2: {card_2}
Card 3: {card_3}

Respond ONLY with a JSON object:
{{
  "caption": "A short engaging caption with an emoji, under 100 characters",
  "hashtags": ["tag1", "tag2", "tag3"]
}}"""

# ─── Prompt Definitions for Admin Seeding ───

DEFAULT_PROMPTS = [
    {
        "prompt_key": "fact_extraction",
        "label": "Prompt 1 — News Fact Extraction",
        "description": "Convert raw news input into structured factual data.",
        "system_prompt": PROMPT_1_SYSTEM,
        "task_prompt": PROMPT_1_TASK,
    },
    {
        "prompt_key": "driver_analysis",
        "label": "Prompt 2 — Driver Analysis (Real Causes)",
        "description": "Identify the deeper structural forces behind the event.",
        "system_prompt": PROMPT_2_SYSTEM,
        "task_prompt": PROMPT_2_TASK,
    },
    {
        "prompt_key": "card_generator",
        "label": "Prompt 3 — WTFHappened Card Generator",
        "description": "Transform structured data into user-facing explanation cards.",
        "system_prompt": PROMPT_3_SYSTEM,
        "task_prompt": PROMPT_3_TASK,
    },
]


def _parse_json(response_text: str) -> dict:
    """Parse JSON from LLM response, stripping markdown if present."""
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


async def _call_llm(system_message: str, user_prompt: str) -> str:
    """Call Claude via Emergent LLM key and return raw response."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not set")

    chat = LlmChat(
        api_key=api_key,
        session_id=f"wtf-{uuid.uuid4().hex[:8]}",
        system_message=system_message,
    )
    chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
    return await chat.send_message(UserMessage(text=user_prompt))


async def _load_prompts(db) -> dict:
    """Load prompts from DB. Returns dict keyed by prompt_key."""
    prompts = await db.ai_prompts.find({}, {"_id": 0}).to_list(10)
    return {p["prompt_key"]: p for p in prompts} if prompts else {}


async def generate_explanation(topic: str, db=None) -> dict:
    """3-step AI pipeline: Extract → Analyze → Generate cards."""

    # Load prompts from DB if available, else use defaults
    prompts = {}
    if db is not None:
        prompts = await _load_prompts(db)

    p1 = prompts.get("fact_extraction", {})
    p2 = prompts.get("driver_analysis", {})
    p3 = prompts.get("card_generator", {})

    # ── Step 1: News Fact Extraction ──
    logger.info(f"Pipeline Step 1: Extracting facts for '{topic[:60]}...'")
    sys1 = p1.get("system_prompt", PROMPT_1_SYSTEM)
    task1 = p1.get("task_prompt", PROMPT_1_TASK)
    resp1 = await _call_llm(sys1, task1.format(topic=topic))
    facts = _parse_json(resp1)

    # ── Step 2: Driver Analysis ──
    logger.info("Pipeline Step 2: Analyzing drivers")
    sys2 = p2.get("system_prompt", PROMPT_2_SYSTEM)
    task2 = p2.get("task_prompt", PROMPT_2_TASK)
    resp2 = await _call_llm(sys2, task2.format(
        event=facts.get("event", ""),
        actors=json.dumps(facts.get("actors", [])),
        causes=json.dumps(facts.get("causes", [])),
        outcomes=json.dumps(facts.get("outcomes", [])),
        implications=json.dumps(facts.get("implications", [])),
    ))
    drivers = _parse_json(resp2)

    # ── Step 3: Card Generation ──
    logger.info("Pipeline Step 3: Generating cards")
    sys3 = p3.get("system_prompt", PROMPT_3_SYSTEM)
    task3 = p3.get("task_prompt", PROMPT_3_TASK)
    resp3 = await _call_llm(sys3, task3.format(
        event=facts.get("event", ""),
        actors=json.dumps(facts.get("actors", [])),
        outcomes=json.dumps(facts.get("outcomes", [])),
        primary_drivers=json.dumps(drivers.get("primary_drivers", [])),
        secondary_drivers=json.dumps(drivers.get("secondary_drivers", [])),
        implications=json.dumps(facts.get("implications", [])),
    ))
    cards = _parse_json(resp3)

    # ── Merge into final output format ──
    category = cards.get("category", facts.get("category", "world_news"))

    # Convert points-based format to text format for compatibility
    card_1_points = cards.get("card_1_points", [])
    card_2_points = cards.get("card_2_points", [])
    card_3_affects = cards.get("card_3_affects", [])
    card_3_action = cards.get("card_3_action", [])

    return {
        "normalized_question": cards.get("normalized_question", topic),
        "card_1": " ".join(card_1_points[:2]) if card_1_points else cards.get("card_1", ""),
        "card_2": " ".join(card_2_points[:2]) if card_2_points else cards.get("card_2", ""),
        "card_3": " ".join(card_3_affects[:2]) if card_3_affects else cards.get("card_3", ""),
        "card_1_detail": " ".join(card_1_points[2:]) if len(card_1_points) > 2 else cards.get("card_1_detail", ""),
        "card_2_detail": " ".join(card_2_points[2:]) if len(card_2_points) > 2 else cards.get("card_2_detail", ""),
        "card_3_detail": " ".join(card_3_action[:2]) if card_3_action else cards.get("card_3_detail", ""),
        "card_3_affects": card_3_affects,
        "card_3_action": card_3_action,
        "category": category,
        # Pipeline metadata
        "_facts": facts,
        "_drivers": drivers,
    }


async def generate_caption(topic: str, card_1: str, card_2: str, card_3: str) -> dict:
    """Generate social media caption for an explanation."""
    try:
        resp = await _call_llm(
            CAPTION_SYSTEM,
            CAPTION_TASK.format(topic=topic, card_1=card_1, card_2=card_2, card_3=card_3),
        )
        return _parse_json(resp)
    except Exception as e:
        logger.error(f"Caption generation failed: {e}")
        return {"caption": f"{topic}", "hashtags": ["trending", "explained"]}
