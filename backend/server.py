from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
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
import PyPDF2
import io

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

UPLOAD_DIR = ROOT_DIR / "uploads" / "pdfs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
    role: str = "user"  # "user" or "admin"
    points: int = 0
    level: int = 1
    streak: int = 0
    last_activity: Optional[str] = None
    badges: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Grade(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    order: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GradeCreate(BaseModel):
    name: str
    order: int

class Subject(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True

class Topic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject_id: str
    name: str
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TopicCreate(BaseModel):
    subject_id: str
    name: str
    description: Optional[str] = None

class Subtopic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic_id: str
    name: str
    description: Optional[str] = None
    knowledge_base_files: List[str] = []  # PDF file paths
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SubtopicCreate(BaseModel):
    topic_id: str
    name: str
    description: Optional[str] = None

class GoogleAuthRequest(BaseModel):
    token: str

class QuizRequest(BaseModel):
    subject: str
    topic: str
    subtopic: Optional[str] = None
    grade: Optional[str] = None
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

async def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ============ PDF Helper ============

def extract_text_from_pdf(pdf_content: bytes) -> str:
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logging.error(f"PDF extraction error: {str(e)}")
        return ""

# ============ Auth Routes ============

@api_router.post("/auth/signup")
async def signup(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        name=user_data.name,
        role="user"
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
    raise HTTPException(status_code=501, detail="Google OAuth integration pending")

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ============ Admin - Subject Management ============

@api_router.get("/admin/subjects")
async def list_subjects(current_user: User = Depends(get_current_user)):
    subjects = await db.subjects.find({}, {"_id": 0}).to_list(1000)
    return subjects

@api_router.post("/admin/subjects")
async def create_subject(subject_data: SubjectCreate, admin: User = Depends(get_current_admin)):
    subject = Subject(**subject_data.model_dump())
    await db.subjects.insert_one(subject.model_dump())
    return subject

@api_router.put("/admin/subjects/{subject_id}")
async def update_subject(subject_id: str, subject_data: SubjectCreate, admin: User = Depends(get_current_admin)):
    result = await db.subjects.update_one(
        {"id": subject_id},
        {"$set": subject_data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"message": "Subject updated successfully"}

@api_router.delete("/admin/subjects/{subject_id}")
async def delete_subject(subject_id: str, admin: User = Depends(get_current_admin)):
    # Also delete related topics and subtopics
    topics = await db.topics.find({"subject_id": subject_id}, {"_id": 0}).to_list(1000)
    topic_ids = [t["id"] for t in topics]
    
    await db.subtopics.delete_many({"topic_id": {"$in": topic_ids}})
    await db.topics.delete_many({"subject_id": subject_id})
    result = await db.subjects.delete_one({"id": subject_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"message": "Subject deleted successfully"}

# ============ Admin - Topic Management ============

@api_router.get("/admin/topics")
async def list_topics(subject_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"subject_id": subject_id} if subject_id else {}
    topics = await db.topics.find(query, {"_id": 0}).to_list(1000)
    return topics

@api_router.post("/admin/topics")
async def create_topic(topic_data: TopicCreate, admin: User = Depends(get_current_admin)):
    # Verify subject exists
    subject = await db.subjects.find_one({"id": topic_data.subject_id}, {"_id": 0})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    topic = Topic(**topic_data.model_dump())
    await db.topics.insert_one(topic.model_dump())
    return topic

@api_router.put("/admin/topics/{topic_id}")
async def update_topic(topic_id: str, topic_data: TopicCreate, admin: User = Depends(get_current_admin)):
    result = await db.topics.update_one(
        {"id": topic_id},
        {"$set": topic_data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic updated successfully"}

@api_router.delete("/admin/topics/{topic_id}")
async def delete_topic(topic_id: str, admin: User = Depends(get_current_admin)):
    # Also delete related subtopics
    await db.subtopics.delete_many({"topic_id": topic_id})
    result = await db.topics.delete_one({"id": topic_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic deleted successfully"}

# ============ Admin - Subtopic Management ============

@api_router.get("/admin/subtopics")
async def list_subtopics(topic_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"topic_id": topic_id} if topic_id else {}
    subtopics = await db.subtopics.find(query, {"_id": 0}).to_list(1000)
    return subtopics

@api_router.post("/admin/subtopics")
async def create_subtopic(subtopic_data: SubtopicCreate, admin: User = Depends(get_current_admin)):
    # Verify topic exists
    topic = await db.topics.find_one({"id": subtopic_data.topic_id}, {"_id": 0})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    subtopic = Subtopic(**subtopic_data.model_dump())
    await db.subtopics.insert_one(subtopic.model_dump())
    return subtopic

@api_router.put("/admin/subtopics/{subtopic_id}")
async def update_subtopic(subtopic_id: str, subtopic_data: SubtopicCreate, admin: User = Depends(get_current_admin)):
    result = await db.subtopics.update_one(
        {"id": subtopic_id},
        {"$set": subtopic_data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    return {"message": "Subtopic updated successfully"}

@api_router.delete("/admin/subtopics/{subtopic_id}")
async def delete_subtopic(subtopic_id: str, admin: User = Depends(get_current_admin)):
    result = await db.subtopics.delete_one({"id": subtopic_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    return {"message": "Subtopic deleted successfully"}

# ============ Admin - PDF Knowledge Base ============

@api_router.post("/admin/subtopics/{subtopic_id}/upload-pdf")
async def upload_pdf(subtopic_id: str, file: UploadFile = File(...), admin: User = Depends(get_current_admin)):
    # Verify subtopic exists
    subtopic = await db.subtopics.find_one({"id": subtopic_id}, {"_id": 0})
    if not subtopic:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save PDF file
    file_id = str(uuid.uuid4())
    file_extension = ".pdf"
    filename = f"{file_id}{file_extension}"
    filepath = UPLOAD_DIR / filename
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Update subtopic with new file
    await db.subtopics.update_one(
        {"id": subtopic_id},
        {"$push": {"knowledge_base_files": filename}}
    )
    
    return {
        "message": "PDF uploaded successfully",
        "filename": file.filename,
        "file_id": filename
    }

@api_router.delete("/admin/subtopics/{subtopic_id}/pdf/{filename}")
async def delete_pdf(subtopic_id: str, filename: str, admin: User = Depends(get_current_admin)):
    # Remove from subtopic
    await db.subtopics.update_one(
        {"id": subtopic_id},
        {"$pull": {"knowledge_base_files": filename}}
    )
    
    # Delete file
    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        filepath.unlink()
    
    return {"message": "PDF deleted successfully"}

# ============ Quiz Generation ============

@api_router.post("/quiz/generate")
async def generate_quiz(request: QuizRequest, current_user: User = Depends(get_current_user)):
    try:
        # Try to find subtopic with knowledge base
        context_text = ""
        if request.subtopic:
            subtopic = await db.subtopics.find_one(
                {"name": request.subtopic, "knowledge_base_files": {"$exists": True, "$ne": []}},
                {"_id": 0}
            )
            
            if subtopic and subtopic.get("knowledge_base_files"):
                # Extract text from PDFs
                for pdf_file in subtopic["knowledge_base_files"][:3]:  # Use up to 3 PDFs
                    filepath = UPLOAD_DIR / pdf_file
                    if filepath.exists():
                        with open(filepath, "rb") as f:
                            pdf_content = f.read()
                            extracted_text = extract_text_from_pdf(pdf_content)
                            if extracted_text:
                                context_text += extracted_text[:3000] + "\n\n"  # Limit per PDF
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"quiz_{uuid.uuid4()}",
            system_message="You are an expert educator creating quiz questions. Generate questions in valid JSON format only."
        ).with_model("gemini", "gemini-3-pro-preview")
        
        context_instruction = ""
        if context_text:
            context_instruction = f"\n\nUSE THIS KNOWLEDGE BASE CONTEXT:\n{context_text[:4000]}\n\nGenerate questions strictly based on this context.\n"
        
        prompt = f"""
Create {request.num_questions} quiz questions for:
Subject: {request.subject}
Topic: {request.topic}
{f'Subtopic: {request.subtopic}' if request.subtopic else ''}
Difficulty: {request.difficulty}
{context_instruction}
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