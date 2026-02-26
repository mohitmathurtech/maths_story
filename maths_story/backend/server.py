"""Focus Learn API — Main application entry point.

All routes are split into modular files under routes/.
This file handles app creation, middleware, and startup.
"""
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

# Load env first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import shared DB
from db import db, client

# Import route modules
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.quiz import router as quiz_router
from routes.daily import router as daily_router
from routes.srs import router as srs_router
from routes.analytics import router as analytics_router
from routes.teacher import router as teacher_router

# ============ App Setup ============

app = FastAPI(title="Focus Learn API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# Mount all route modules
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(quiz_router)
api_router.include_router(daily_router)
api_router.include_router(srs_router)
api_router.include_router(analytics_router)
api_router.include_router(teacher_router)

@api_router.get("/")
async def root():
    return {"message": "Focus Learn API", "status": "running"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Logging ============

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ Startup / Shutdown ============

@app.on_event("startup")
async def startup_init():
    """Create MongoDB indexes and run initialization."""
    await db.users.create_index("id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.quizzes.create_index("id", unique=True)
    await db.quizzes.create_index("user_id")
    await db.quizzes.create_index([("user_id", 1), ("created_at", -1)])
    await db.quiz_results.create_index("id", unique=True)
    await db.quiz_results.create_index("user_id")
    await db.quiz_results.create_index([("subject", 1), ("topic", 1)])
    await db.quiz_results.create_index([("user_id", 1), ("subject", 1), ("score", 1)])
    await db.subtopics.create_index("name")
    await db.subtopics.create_index("topic_id")
    await db.topics.create_index("subject_id")
    await db.grades.create_index("order")
    await db.question_bank.create_index([("subject", 1), ("topic", 1), ("difficulty", 1)])
    await db.question_bank.create_index("question")
    await db.knowledge_chunks.create_index("subtopic_name")
    # New indexes for new features
    await db.srs_cards.create_index([("user_id", 1), ("next_review", 1)])
    await db.srs_cards.create_index("id", unique=True)
    await db.daily_challenges.create_index("date", unique=True)
    await db.daily_submissions.create_index([("user_id", 1), ("date", 1)], unique=True)
    logging.info("MongoDB indexes created successfully")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()