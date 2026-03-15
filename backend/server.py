from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext

from services.ai_engine import generate_explanation, generate_caption
from services.data_collector import get_seed_topics, SEED_EXPLANATIONS, collect_all_trending

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Auth config
JWT_SECRET = os.environ.get("JWT_SECRET", uuid.uuid4().hex + uuid.uuid4().hex)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Auth Models ---

class RegisterRequest(BaseModel):
    email: Optional[str] = None
    mobile: Optional[str] = None
    password: str
    name: str

class LoginRequest(BaseModel):
    identifier: str  # email or mobile
    password: str

class OnboardingRequest(BaseModel):
    interests: List[str] = []
    curiosity_types: List[str] = []
    explanation_depth: str = "simple"
    country: str = ""
    region: str = ""
    professional_context: str = ""
    followed_topics: List[str] = []

# --- Auth Helpers ---

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_optional_user(authorization: Optional[str] = Header(None)):
    """Returns user if authenticated, None otherwise."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        user_id = verify_token(token)
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        return user
    except Exception:
        return None

# --- Auth Routes ---

@api_router.post("/auth/register")
async def register(req: RegisterRequest):
    if not req.email and not req.mobile:
        raise HTTPException(status_code=400, detail="Email or mobile is required")

    # Check existing user
    query = []
    if req.email:
        query.append({"email": req.email.lower().strip()})
    if req.mobile:
        query.append({"mobile": req.mobile.strip()})

    existing = await db.users.find_one({"$or": query})
    if existing:
        raise HTTPException(status_code=409, detail="User already exists with this email or mobile")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    user = {
        "id": user_id,
        "name": req.name.strip(),
        "email": req.email.lower().strip() if req.email else None,
        "mobile": req.mobile.strip() if req.mobile else None,
        "password_hash": pwd_context.hash(req.password),
        "onboarding_complete": False,
        "preferences": {},
        "created_at": now,
    }
    await db.users.insert_one({**user})

    token = create_token(user_id)
    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "mobile": user["mobile"],
            "onboarding_complete": False,
            "preferences": {},
        }
    }

@api_router.post("/auth/login")
async def login(req: LoginRequest):
    identifier = req.identifier.strip().lower()
    user = await db.users.find_one({
        "$or": [{"email": identifier}, {"mobile": identifier}]
    })
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user["id"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user.get("email"),
            "mobile": user.get("mobile"),
            "onboarding_complete": user.get("onboarding_complete", False),
            "preferences": user.get("preferences", {}),
        }
    }

@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return {"user": user}

@api_router.put("/auth/onboarding")
async def save_onboarding(req: OnboardingRequest, user=Depends(get_current_user)):
    preferences = {
        "interests": req.interests,
        "curiosity_types": req.curiosity_types,
        "explanation_depth": req.explanation_depth,
        "country": req.country,
        "region": req.region,
        "professional_context": req.professional_context,
        "followed_topics": req.followed_topics,
    }
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"preferences": preferences, "onboarding_complete": True}}
    )
    return {"message": "Onboarding complete", "preferences": preferences}

# --- Content Models ---

class TopicOut(BaseModel):
    id: str
    title: str
    category: str
    source: str
    trend_score: float
    created_at: str
    has_explanation: bool = False

class ExplanationOut(BaseModel):
    id: str
    topic_id: str
    topic_title: str
    normalized_question: str
    card_1: str
    card_2: str
    card_3: str
    card_1_detail: str
    card_2_detail: str
    card_3_detail: str
    category: str
    visual_type: Optional[str] = None
    created_at: str

class ExplainRequest(BaseModel):
    input: str

class SaveRequest(BaseModel):
    topic_id: str

class RenderCardRequest(BaseModel):
    topic_id: str
    template_type: str = "standard"

# --- Helpers ---

def time_ago(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str)
        now = datetime.now(timezone.utc)
        diff = now - dt
        hours = int(diff.total_seconds() / 3600)
        if hours < 1:
            mins = int(diff.total_seconds() / 60)
            return f"{max(1, mins)}m ago"
        if hours < 24:
            return f"{hours}h ago"
        days = int(hours / 24)
        return f"{days}d ago"
    except Exception:
        return "recently"

# --- Routes ---

@api_router.get("/")
async def root():
    return {"message": "WTFHappened API", "status": "running"}

@api_router.get("/health")
async def health():
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "disconnected"}

@api_router.get("/feed")
async def get_feed(limit: int = 20, category: Optional[str] = None):
    """Get trending topics feed, sorted by trend score."""
    query = {}
    if category and category != "all":
        query["category"] = category

    topics = await db.topics.find(query, {"_id": 0}).sort("trend_score", -1).limit(limit).to_list(limit)

    # Check which have explanations
    for t in topics:
        exp = await db.explanations.find_one({"topic_id": t["id"]}, {"_id": 0, "id": 1})
        t["has_explanation"] = exp is not None
        t["time_ago"] = time_ago(t.get("created_at", ""))

    return {"topics": topics}

@api_router.get("/explanation/{topic_id}")
async def get_explanation(topic_id: str):
    """Get explanation cards for a topic."""
    explanation = await db.explanations.find_one({"topic_id": topic_id}, {"_id": 0})
    if not explanation:
        # Try to generate one
        topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        try:
            ai_result = await generate_explanation(topic["title"])
            explanation = {
                "id": str(uuid.uuid4()),
                "topic_id": topic_id,
                "topic_title": topic["title"],
                "normalized_question": ai_result.get("normalized_question", topic["title"]),
                "card_1": ai_result["card_1"],
                "card_2": ai_result["card_2"],
                "card_3": ai_result["card_3"],
                "card_1_detail": ai_result.get("card_1_detail", ""),
                "card_2_detail": ai_result.get("card_2_detail", ""),
                "card_3_detail": ai_result.get("card_3_detail", ""),
                "category": ai_result.get("category", topic.get("category", "world_news")),
                "visual_type": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            doc_to_insert = {**explanation}
            await db.explanations.insert_one(doc_to_insert)
            explanation.pop("_id", None)
        except Exception as e:
            logging.error(f"Explanation generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

    return {"explanation": explanation}

@api_router.post("/explain")
async def explain_topic(req: ExplainRequest):
    """Generate explanation from user input (headline/question)."""
    user_input = req.input.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Input is required")

    try:
        ai_result = await generate_explanation(user_input)

        # Create topic
        topic_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        category = ai_result.get("category", "world_news")

        topic = {
            "id": topic_id,
            "title": user_input,
            "category": category,
            "source": "user_input",
            "trend_score": 50,
            "created_at": now,
        }
        await db.topics.insert_one({**topic})

        explanation = {
            "id": str(uuid.uuid4()),
            "topic_id": topic_id,
            "topic_title": user_input,
            "normalized_question": ai_result.get("normalized_question", user_input),
            "card_1": ai_result["card_1"],
            "card_2": ai_result["card_2"],
            "card_3": ai_result["card_3"],
            "card_1_detail": ai_result.get("card_1_detail", ""),
            "card_2_detail": ai_result.get("card_2_detail", ""),
            "card_3_detail": ai_result.get("card_3_detail", ""),
            "category": category,
            "visual_type": None,
            "created_at": now,
        }
        await db.explanations.insert_one({**explanation})

        # Remove _id from response
        topic.pop("_id", None)
        explanation.pop("_id", None)

        return {"topic": topic, "explanation": explanation}

    except Exception as e:
        logging.error(f"Explain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trending")
async def get_trending(limit: int = 10):
    """Get trending confusion index - topics people are searching/asking about."""
    topics = await db.topics.find({}, {"_id": 0}).sort("trend_score", -1).limit(limit).to_list(limit)
    for t in topics:
        t["time_ago"] = time_ago(t.get("created_at", ""))
    return {"trending": topics}

@api_router.post("/save/{topic_id}")
async def save_topic(topic_id: str, user=Depends(get_current_user)):
    """Save/bookmark a topic for the authenticated user."""
    topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    existing = await db.saved_topics.find_one({"topic_id": topic_id, "user_id": user["id"]})
    if existing:
        await db.saved_topics.delete_one({"topic_id": topic_id, "user_id": user["id"]})
        return {"saved": False, "message": "Topic removed from saved"}

    saved = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "topic_id": topic_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.saved_topics.insert_one(saved)
    return {"saved": True, "message": "Topic saved"}

@api_router.get("/saved")
async def get_saved(user=Depends(get_current_user)):
    """Get saved topics for the authenticated user."""
    saved_items = await db.saved_topics.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("saved_at", -1).to_list(100)
    result = []
    for item in saved_items:
        topic = await db.topics.find_one({"id": item["topic_id"]}, {"_id": 0})
        if topic:
            explanation = await db.explanations.find_one({"topic_id": item["topic_id"]}, {"_id": 0})
            result.append({
                "topic": topic,
                "explanation": explanation,
                "saved_at": item.get("saved_at", ""),
            })
    return {"saved": result}

@api_router.get("/render-card/{topic_id}")
async def render_card(topic_id: str, template_type: str = "standard"):
    """Get social card data for a topic."""
    explanation = await db.explanations.find_one({"topic_id": topic_id}, {"_id": 0})
    if not explanation:
        raise HTTPException(status_code=404, detail="Explanation not found")

    topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
    title = topic["title"] if topic else explanation.get("topic_title", "")

    # Generate caption
    caption_data = await generate_caption(
        title, explanation["card_1"], explanation["card_2"], explanation["card_3"]
    )

    # Category colors
    category_colors = {
        "technology": {"bg": "#EBF5FF", "accent": "#3B82F6"},
        "finance": {"bg": "#F0FDF4", "accent": "#22C55E"},
        "economy": {"bg": "#FFFBEB", "accent": "#F59E0B"},
        "ai": {"bg": "#F3E8FF", "accent": "#8B5CF6"},
        "crypto": {"bg": "#FFF7ED", "accent": "#F97316"},
        "science": {"bg": "#EDE9FE", "accent": "#7C3AED"},
        "world_news": {"bg": "#FEF2F2", "accent": "#EF4444"},
        "internet_culture": {"bg": "#FFF1F2", "accent": "#F43F5E"},
        "politics": {"bg": "#FEF2F2", "accent": "#DC2626"},
    }

    category = explanation.get("category", "world_news")
    colors = category_colors.get(category, {"bg": "#F5F5F5", "accent": "#6B7280"})

    # Template sizes
    templates = {
        "standard": {"width": 1080, "height": 1080, "platform": "Instagram/LinkedIn"},
        "twitter": {"width": 1200, "height": 675, "platform": "X/Twitter"},
        "story": {"width": 1080, "height": 1920, "platform": "Stories/Reels"},
    }
    template = templates.get(template_type, templates["standard"])

    return {
        "card_data": {
            "title": title,
            "card_1": explanation["card_1"],
            "card_2": explanation["card_2"],
            "card_3": explanation["card_3"],
            "category": category,
            "colors": colors,
            "template": template,
            "template_type": template_type,
            "caption": caption_data.get("caption", ""),
            "hashtags": caption_data.get("hashtags", []),
            "brand": "wtfhappened.app",
        }
    }

@api_router.post("/refresh-trending")
async def refresh_trending(background_tasks: BackgroundTasks):
    """Trigger a refresh of trending data from external sources."""
    background_tasks.add_task(ingest_trending_data)
    return {"message": "Refresh started"}

# --- Data Seeding ---

async def seed_initial_data():
    """Seed the database with initial topics and explanations."""
    count = await db.topics.count_documents({})
    if count > 0:
        return

    logging.info("Seeding initial data...")
    seed_topics = get_seed_topics()
    now = datetime.now(timezone.utc).isoformat()

    for topic_data in seed_topics:
        topic_id = str(uuid.uuid4())
        topic = {
            "id": topic_id,
            "title": topic_data["title"],
            "category": topic_data["category"],
            "source": topic_data["source"],
            "trend_score": topic_data["trend_score"],
            "created_at": now,
        }
        await db.topics.insert_one(topic)

        # Add seed explanation if available
        if topic_data["title"] in SEED_EXPLANATIONS:
            exp_data = SEED_EXPLANATIONS[topic_data["title"]]
            explanation = {
                "id": str(uuid.uuid4()),
                "topic_id": topic_id,
                "topic_title": topic_data["title"],
                "normalized_question": f"Why: {topic_data['title']}?",
                "card_1": exp_data["card_1"],
                "card_2": exp_data["card_2"],
                "card_3": exp_data["card_3"],
                "card_1_detail": exp_data.get("card_1_detail", ""),
                "card_2_detail": exp_data.get("card_2_detail", ""),
                "card_3_detail": exp_data.get("card_3_detail", ""),
                "category": exp_data.get("category", topic_data["category"]),
                "visual_type": None,
                "created_at": now,
            }
            await db.explanations.insert_one(explanation)

    logging.info(f"Seeded {len(seed_topics)} topics")


async def ingest_trending_data():
    """Fetch and store trending topics from external sources."""
    try:
        new_topics = await collect_all_trending()
        now = datetime.now(timezone.utc).isoformat()
        added = 0
        for topic_data in new_topics:
            # Check for duplicate titles
            existing = await db.topics.find_one({"title": topic_data["title"]})
            if existing:
                continue
            topic = {
                "id": str(uuid.uuid4()),
                "title": topic_data["title"],
                "category": topic_data["category"],
                "source": topic_data["source"],
                "trend_score": topic_data["trend_score"],
                "created_at": now,
            }
            await db.topics.insert_one(topic)
            added += 1
        logging.info(f"Ingested {added} new trending topics")
    except Exception as e:
        logging.error(f"Trending data ingestion failed: {e}")


# --- App Events ---

@app.on_event("startup")
async def startup():
    # Create indexes
    await db.topics.create_index("id", unique=True)
    await db.topics.create_index("trend_score")
    await db.topics.create_index("category")
    await db.explanations.create_index("topic_id")
    await db.saved_topics.create_index("topic_id")
    await db.saved_topics.create_index("user_id")
    await db.users.create_index("id", unique=True)
    await db.users.create_index("email", sparse=True)
    await db.users.create_index("mobile", sparse=True)
    # Seed data
    await seed_initial_data()
    logging.info("WTFHappened API started")

@app.on_event("shutdown")
async def shutdown():
    client.close()

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
