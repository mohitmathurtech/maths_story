"""Admin routes — grades, subjects, topics, subtopics, PDF management."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional
import uuid

from db import db, UPLOAD_DIR
from models import (
    User, Grade, GradeCreate, Subject, SubjectCreate,
    Topic, TopicCreate, Subtopic, SubtopicCreate
)
from utils.auth import get_current_user, get_current_admin
from utils.pdf import rebuild_subtopic_text_cache

router = APIRouter(prefix="/admin", tags=["admin"])

# ---- Grades ----

@router.get("/grades")
async def list_grades(current_user: User = Depends(get_current_user)):
    return await db.grades.find({}, {"_id": 0}).sort("order", 1).to_list(1000)

@router.post("/grades")
async def create_grade(grade_data: GradeCreate, admin: User = Depends(get_current_admin)):
    grade = Grade(**grade_data.model_dump())
    await db.grades.insert_one(grade.model_dump())
    return grade

@router.put("/grades/{grade_id}")
async def update_grade(grade_id: str, grade_data: GradeCreate, admin: User = Depends(get_current_admin)):
    result = await db.grades.update_one({"id": grade_id}, {"$set": grade_data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Grade not found")
    return {"message": "Grade updated successfully"}

@router.delete("/grades/{grade_id}")
async def delete_grade(grade_id: str, admin: User = Depends(get_current_admin)):
    result = await db.grades.delete_one({"id": grade_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Grade not found")
    return {"message": "Grade deleted successfully"}

# ---- Subjects ----

@router.get("/subjects")
async def list_subjects(current_user: User = Depends(get_current_user)):
    return await db.subjects.find({}, {"_id": 0}).to_list(1000)

@router.post("/subjects")
async def create_subject(subject_data: SubjectCreate, admin: User = Depends(get_current_admin)):
    subject = Subject(**subject_data.model_dump())
    await db.subjects.insert_one(subject.model_dump())
    return subject

@router.put("/subjects/{subject_id}")
async def update_subject(subject_id: str, subject_data: SubjectCreate, admin: User = Depends(get_current_admin)):
    result = await db.subjects.update_one({"id": subject_id}, {"$set": subject_data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"message": "Subject updated successfully"}

@router.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: str, admin: User = Depends(get_current_admin)):
    topics = await db.topics.find({"subject_id": subject_id}, {"_id": 0}).to_list(1000)
    topic_ids = [t["id"] for t in topics]
    await db.subtopics.delete_many({"topic_id": {"$in": topic_ids}})
    await db.topics.delete_many({"subject_id": subject_id})
    result = await db.subjects.delete_one({"id": subject_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"message": "Subject deleted successfully"}

# ---- Topics ----

@router.get("/topics")
async def list_topics(subject_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"subject_id": subject_id} if subject_id else {}
    return await db.topics.find(query, {"_id": 0}).to_list(1000)

@router.post("/topics")
async def create_topic(topic_data: TopicCreate, admin: User = Depends(get_current_admin)):
    subject = await db.subjects.find_one({"id": topic_data.subject_id}, {"_id": 0})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    topic = Topic(**topic_data.model_dump())
    await db.topics.insert_one(topic.model_dump())
    return topic

@router.put("/topics/{topic_id}")
async def update_topic(topic_id: str, topic_data: TopicCreate, admin: User = Depends(get_current_admin)):
    result = await db.topics.update_one({"id": topic_id}, {"$set": topic_data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic updated successfully"}

@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, admin: User = Depends(get_current_admin)):
    await db.subtopics.delete_many({"topic_id": topic_id})
    result = await db.topics.delete_one({"id": topic_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic deleted successfully"}

# ---- Subtopics ----

@router.get("/subtopics")
async def list_subtopics(topic_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"topic_id": topic_id} if topic_id else {}
    return await db.subtopics.find(query, {"_id": 0}).to_list(1000)

@router.post("/subtopics")
async def create_subtopic(subtopic_data: SubtopicCreate, admin: User = Depends(get_current_admin)):
    topic = await db.topics.find_one({"id": subtopic_data.topic_id}, {"_id": 0})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    subtopic = Subtopic(**subtopic_data.model_dump())
    await db.subtopics.insert_one(subtopic.model_dump())
    return subtopic

@router.put("/subtopics/{subtopic_id}")
async def update_subtopic(subtopic_id: str, subtopic_data: SubtopicCreate, admin: User = Depends(get_current_admin)):
    result = await db.subtopics.update_one({"id": subtopic_id}, {"$set": subtopic_data.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    return {"message": "Subtopic updated successfully"}

@router.delete("/subtopics/{subtopic_id}")
async def delete_subtopic(subtopic_id: str, admin: User = Depends(get_current_admin)):
    result = await db.subtopics.delete_one({"id": subtopic_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    return {"message": "Subtopic deleted successfully"}

# ---- PDF upload/delete ----

@router.post("/subtopics/{subtopic_id}/upload-pdf")
async def upload_pdf(subtopic_id: str, file: UploadFile = File(...), admin: User = Depends(get_current_admin)):
    subtopic = await db.subtopics.find_one({"id": subtopic_id}, {"_id": 0})
    if not subtopic:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_id = str(uuid.uuid4())
    filename = f"{file_id}.pdf"
    filepath = UPLOAD_DIR / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    await db.subtopics.update_one({"id": subtopic_id}, {"$push": {"knowledge_base_files": filename}})
    await rebuild_subtopic_text_cache(subtopic_id)

    return {"message": "PDF uploaded successfully", "filename": file.filename, "file_id": filename}

@router.delete("/subtopics/{subtopic_id}/pdf/{filename}")
async def delete_pdf(subtopic_id: str, filename: str, admin: User = Depends(get_current_admin)):
    await db.subtopics.update_one({"id": subtopic_id}, {"$pull": {"knowledge_base_files": filename}})
    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        filepath.unlink()
    await rebuild_subtopic_text_cache(subtopic_id)
    return {"message": "PDF deleted successfully"}
