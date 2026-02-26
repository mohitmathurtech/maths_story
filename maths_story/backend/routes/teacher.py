"""Teacher dashboard routes — class management and student analytics."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from db import db
from models import User
from utils.auth import get_current_user

router = APIRouter(prefix="/teacher", tags=["teacher"])


# ---- Models ----

class ClassCreate(BaseModel):
    name: str
    description: str = ""

class ClassInvite(BaseModel):
    student_email: str

class QuizAssignment(BaseModel):
    class_id: str
    subject: str
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5
    due_date: Optional[str] = None


# ---- Helpers ----

def require_teacher(user: User):
    if user.role not in ("teacher", "admin"):
        raise HTTPException(403, "Teacher access required")
    return user


# ---- Endpoints ----

@router.post("/classes")
async def create_class(data: ClassCreate, current_user: User = Depends(get_current_user)):
    require_teacher(current_user)
    cls = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description,
        "teacher_id": current_user.id,
        "teacher_name": current_user.name,
        "student_ids": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.classes.insert_one(cls)
    cls.pop("_id", None)
    return cls


@router.get("/classes")
async def list_classes(current_user: User = Depends(get_current_user)):
    require_teacher(current_user)
    classes = await db.classes.find(
        {"teacher_id": current_user.id}, {"_id": 0}
    ).to_list(100)
    # Add student count
    for c in classes:
        c["student_count"] = len(c.get("student_ids", []))
    return classes


@router.post("/classes/{class_id}/invite")
async def invite_student(class_id: str, data: ClassInvite, current_user: User = Depends(get_current_user)):
    require_teacher(current_user)
    cls = await db.classes.find_one({"id": class_id, "teacher_id": current_user.id})
    if not cls:
        raise HTTPException(404, "Class not found")

    student = await db.users.find_one({"email": data.student_email})
    if not student:
        raise HTTPException(404, "Student not found")

    if student["id"] in cls.get("student_ids", []):
        raise HTTPException(400, "Student already in class")

    await db.classes.update_one(
        {"id": class_id},
        {"$push": {"student_ids": student["id"]}}
    )
    return {"message": f"{student['name']} added to {cls['name']}"}


@router.get("/classes/{class_id}/students")
async def get_class_students(class_id: str, current_user: User = Depends(get_current_user)):
    require_teacher(current_user)
    cls = await db.classes.find_one({"id": class_id, "teacher_id": current_user.id})
    if not cls:
        raise HTTPException(404, "Class not found")

    student_ids = cls.get("student_ids", [])
    students = []
    for sid in student_ids:
        user = await db.users.find_one({"id": sid}, {"_id": 0, "password": 0})
        if user:
            # Get quiz stats
            results = await db.quiz_results.find({"user_id": sid}).to_list(1000)
            user["total_quizzes"] = len(results)
            user["avg_score"] = round(
                sum(r.get("score", 0) for r in results) / len(results), 1
            ) if results else 0
            # Weak topics (score < 60)
            weak = {}
            for r in results:
                if r.get("score", 100) < 60:
                    key = f"{r['subject']}: {r['topic']}"
                    weak[key] = weak.get(key, 0) + 1
            user["weak_topics"] = sorted(weak.keys(), key=lambda k: weak[k], reverse=True)[:3]
            students.append(user)

    return students


@router.get("/classes/{class_id}/analytics")
async def get_class_analytics(class_id: str, current_user: User = Depends(get_current_user)):
    require_teacher(current_user)
    cls = await db.classes.find_one({"id": class_id, "teacher_id": current_user.id})
    if not cls:
        raise HTTPException(404, "Class not found")

    student_ids = cls.get("student_ids", [])
    all_results = []
    for sid in student_ids:
        results = await db.quiz_results.find({"user_id": sid}).to_list(1000)
        all_results.extend(results)

    if not all_results:
        return {"class_avg_score": 0, "total_quizzes": 0, "topic_breakdown": [], "daily_activity": []}

    class_avg = round(sum(r.get("score", 0) for r in all_results) / len(all_results), 1)

    # Topic breakdown
    topics = {}
    for r in all_results:
        key = f"{r.get('subject','')}: {r.get('topic','')}"
        if key not in topics:
            topics[key] = {"scores": [], "count": 0}
        topics[key]["scores"].append(r.get("score", 0))
        topics[key]["count"] += 1

    topic_breakdown = [
        {"topic": k, "avg_score": round(sum(v["scores"])/len(v["scores"]), 1), "attempts": v["count"]}
        for k, v in sorted(topics.items(), key=lambda x: sum(x[1]["scores"])/len(x[1]["scores"]))
    ]

    return {
        "class_name": cls["name"],
        "student_count": len(student_ids),
        "total_quizzes": len(all_results),
        "class_avg_score": class_avg,
        "topic_breakdown": topic_breakdown,
    }


@router.post("/classes/{class_id}/assign")
async def assign_quiz(class_id: str, data: QuizAssignment, current_user: User = Depends(get_current_user)):
    require_teacher(current_user)
    cls = await db.classes.find_one({"id": class_id, "teacher_id": current_user.id})
    if not cls:
        raise HTTPException(404, "Class not found")

    assignment = {
        "id": str(uuid.uuid4()),
        "class_id": class_id,
        "teacher_id": current_user.id,
        "subject": data.subject,
        "topic": data.topic,
        "difficulty": data.difficulty,
        "num_questions": data.num_questions,
        "due_date": data.due_date,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "student_submissions": [],
    }
    await db.assignments.insert_one(assignment)
    assignment.pop("_id", None)
    return assignment


@router.get("/assignments/{class_id}")
async def get_assignments(class_id: str, current_user: User = Depends(get_current_user)):
    require_teacher(current_user)
    assignments = await db.assignments.find(
        {"class_id": class_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return assignments
