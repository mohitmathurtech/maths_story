"""Pydantic models for all entities."""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone


# ============ Auth Models ============

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
    role: str = "user"
    points: int = 0
    level: int = 1
    streak: int = 0
    last_activity: Optional[str] = None
    badges: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GoogleAuthRequest(BaseModel):
    token: str

# ============ Admin / Content Models ============

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
    knowledge_base_files: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SubtopicCreate(BaseModel):
    topic_id: str
    name: str
    description: Optional[str] = None

# ============ Quiz Models ============

class QuizRequest(BaseModel):
    subject: str
    topic: str
    subtopic: Optional[str] = None
    grade: Optional[str] = None
    difficulty: str = "medium"
    num_questions: int = 5
    mode: str = "timed"  # "timed", "practice", "exam"
    story_mode: bool = False  # Enable narrative-based questions

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
    mode: str = "timed"
    story_mode: bool = False
    questions: List[Dict]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class QuizAnswer(BaseModel):
    question_id: str
    user_answer: str
    time_taken: float
    is_correct: bool = False  # Ignored — server validates server-side

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
    answers_detail: List[Dict] = []  # Per-question breakdown
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============ Daily Challenge Models ============

class DailyChallenge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str  # YYYY-MM-DD
    subject: str
    topic: str
    difficulty: str = "medium"
    questions: List[Dict] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============ SRS Models ============

class SRSCard(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    question: Dict  # Full question data
    subject: str
    topic: str
    bucket: int = 0  # Leitner box 0-4
    next_review: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    times_reviewed: int = 0
    times_correct: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
