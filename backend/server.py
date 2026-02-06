from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# ============ Models ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    points: int = 0
    level: int = 1
    streak: int = 0
    last_activity: Optional[str] = None
    badges: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GoogleAuthRequest(BaseModel):
    token: str

class QuizRequest(BaseModel):
    subject: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: str = "medium"
    num_questions: int = 5

class QuizQuestion(BaseModel):
    id: str
    question: str
    type: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None

class Quiz(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subject: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: str
    questions: List[Dict]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class QuizAnswer(BaseModel):
    question_id: str
    user_answer: str
    time_taken: float
    is_correct: bool

class QuizSubmission(BaseModel):
    quiz_id: str
    answers: List[QuizAnswer]

class QuizResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quiz_id: str
    user_id: str
    subject: str
    topic: str
    subtopic: Optional[str] = None
    score: float
    total_questions: int
    correct_answers: int
    avg_time: float
    focus_score: float
    points_earned: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============ Auth Helpers ============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ Auth Routes ============

@api_router.post("/auth/signup")
async def signup(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        name=user_data.name
    )
    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    token = create_access_token({"sub": user.id})
    return {"token": token, "user": user.model_dump()}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_obj = User(**{k: v for k, v in user.items() if k != "password"})
    token = create_access_token({"sub": user_obj.id})
    return {"token": token, "user": user_obj.model_dump()}

@api_router.post("/auth/google")
async def google_auth(auth_request: GoogleAuthRequest):
    # Placeholder for Emergent Google OAuth integration
    # In production, validate token with Google/Emergent service
    raise HTTPException(status_code=501, detail="Google OAuth integration pending")

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ============ Quiz Generation ============

@api_router.post("/quiz/generate")
async def generate_quiz(request: QuizRequest, current_user: User = Depends(get_current_user)):
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"quiz_{uuid.uuid4()}",
            system_message="You are an expert educator creating quiz questions. Generate questions in valid JSON format only."
        ).with_model("gemini", "gemini-3-pro-preview")
        
        prompt = f"""
Create {request.num_questions} quiz questions for:
Subject: {request.subject}
Topic: {request.topic}
{f'Subtopic: {request.subtopic}' if request.subtopic else ''}
Difficulty: {request.difficulty}

For each question, include:
1. question text
2. type ("mcq" or "alphanumeric")
3. options (array of 4 options for MCQ, empty for alphanumeric)
4. correct_answer (option letter for MCQ, actual answer for alphanumeric)
5. explanation

Return ONLY valid JSON array with this structure:
[
  {{
    "question": "...",
    "type": "mcq",
    "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
    "correct_answer": "A",
    "explanation": "..."
  }}
]
"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse JSON from response
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        questions_data = json.loads(response_text)
        
        # Add IDs to questions
        for q in questions_data:
            q["id"] = str(uuid.uuid4())
        
        quiz = Quiz(
            user_id=current_user.id,
            subject=request.subject,
            topic=request.topic,
            subtopic=request.subtopic,
            difficulty=request.difficulty,
            questions=questions_data
        )
        
        await db.quizzes.insert_one(quiz.model_dump())
        
        # Return quiz without correct answers
        quiz_response = quiz.model_dump()
        for q in quiz_response["questions"]:
            q.pop("correct_answer", None)
            q.pop("explanation", None)
        
        return quiz_response
        
    except Exception as e:
        logging.error(f"Quiz generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@api_router.post("/quiz/submit")
async def submit_quiz(submission: QuizSubmission, current_user: User = Depends(get_current_user)):
    quiz = await db.quizzes.find_one({"id": submission.quiz_id}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    if quiz["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Calculate results
    correct_count = 0
    total_time = 0
    time_variance = []
    
    questions_dict = {q["id"]: q for q in quiz["questions"]}
    
    for answer in submission.answers:
        question = questions_dict.get(answer.question_id)
        if question and answer.is_correct:
            correct_count += 1
        total_time += answer.time_taken
        time_variance.append(answer.time_taken)
    
    avg_time = total_time / len(submission.answers) if submission.answers else 0
    
    # Calculate focus score (lower variance = higher focus)
    if len(time_variance) > 1:
        variance = sum((t - avg_time) ** 2 for t in time_variance) / len(time_variance)
        focus_score = max(0, min(100, 100 - (variance / 10)))
    else:
        focus_score = 80
    
    score = (correct_count / len(submission.answers)) * 100 if submission.answers else 0
    points_earned = int(correct_count * 10 + focus_score / 10)
    
    # Update user stats
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$inc": {"points": points_earned},
            "$set": {"last_activity": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Check level up
    updated_user = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    new_level = (updated_user["points"] // 100) + 1
    if new_level > updated_user["level"]:
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"level": new_level}}
        )
    
    result = QuizResult(
        quiz_id=submission.quiz_id,
        user_id=current_user.id,
        subject=quiz["subject"],
        topic=quiz["topic"],
        subtopic=quiz.get("subtopic"),
        score=score,
        total_questions=len(submission.answers),
        correct_answers=correct_count,
        avg_time=avg_time,
        focus_score=focus_score,
        points_earned=points_earned
    )
    
    await db.quiz_results.insert_one(result.model_dump())
    
    # Return result with explanations
    result_dict = result.model_dump()
    result_dict["explanations"] = [
        {
            "question_id": q["id"],
            "question": q["question"],
            "correct_answer": q["correct_answer"],
            "explanation": q.get("explanation", "")
        }
        for q in quiz["questions"]
    ]
    
    return result_dict

# ============ Analytics Routes ============

@api_router.get("/analytics/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    results = await db.quiz_results.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    
    total_quizzes = len(results)
    avg_score = sum(r["score"] for r in results) / total_quizzes if total_quizzes > 0 else 0
    avg_focus = sum(r["focus_score"] for r in results) / total_quizzes if total_quizzes > 0 else 0
    
    # Topic performance
    topic_stats = {}
    for r in results:
        key = f"{r['subject']}:{r['topic']}"
        if key not in topic_stats:
            topic_stats[key] = {"subject": r["subject"], "topic": r["topic"], "scores": [], "count": 0}
        topic_stats[key]["scores"].append(r["score"])
        topic_stats[key]["count"] += 1
    
    topic_performance = [
        {
            "subject": v["subject"],
            "topic": v["topic"],
            "avg_score": sum(v["scores"]) / len(v["scores"]),
            "attempts": v["count"]
        }
        for v in topic_stats.values()
    ]
    
    return {
        "total_quizzes": total_quizzes,
        "avg_score": round(avg_score, 1),
        "avg_focus": round(avg_focus, 1),
        "points": current_user.points,
        "level": current_user.level,
        "streak": current_user.streak,
        "topic_performance": topic_performance,
        "recent_results": results[-5:] if len(results) > 5 else results
    }

@api_router.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    users = await db.users.find({}, {"_id": 0, "password": 0}).sort("points", -1).limit(limit).to_list(limit)
    return users

@api_router.get("/leaderboard/topic/{subject}/{topic}")
async def get_topic_leaderboard(subject: str, topic: str, limit: int = 10):
    pipeline = [
        {"$match": {"subject": subject, "topic": topic}},
        {"$group": {
            "_id": "$user_id",
            "avg_score": {"$avg": "$score"},
            "total_attempts": {"$sum": 1}
        }},
        {"$sort": {"avg_score": -1}},
        {"$limit": limit}
    ]
    
    results = await db.quiz_results.aggregate(pipeline).to_list(limit)
    
    # Enrich with user data
    leaderboard = []
    for r in results:
        user = await db.users.find_one({"id": r["_id"]}, {"_id": 0, "password": 0})
        if user:
            leaderboard.append({
                "user": {"name": user["name"], "level": user["level"]},
                "avg_score": round(r["avg_score"], 1),
                "total_attempts": r["total_attempts"]
            })
    
    return leaderboard

# ============ Root Routes ============

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()