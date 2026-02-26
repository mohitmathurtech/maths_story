"""Daily Challenge routes — one curated challenge per day."""
from fastapi import APIRouter, HTTPException, Depends
from emergentintegrations.llm.chat import LlmChat, UserMessage
from datetime import datetime, timezone
import json
import uuid
import logging
import os
import random

from db import db
from models import User, DailyChallenge
from utils.auth import get_current_user

router = APIRouter(prefix="/daily", tags=["daily-challenge"])

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Rotating subjects for daily challenges
DAILY_SUBJECTS = [
    {"subject": "Mathematics", "topic": "Mental Math"},
    {"subject": "Mathematics", "topic": "Logic Puzzles"},
    {"subject": "Science", "topic": "General Knowledge"},
    {"subject": "Mathematics", "topic": "Word Problems"},
    {"subject": "Science", "topic": "Scientific Reasoning"},
    {"subject": "Mathematics", "topic": "Number Patterns"},
    {"subject": "Mathematics", "topic": "Geometry Basics"},
]


async def _ensure_daily_challenge() -> dict:
    """Get or create today's daily challenge."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    existing = await db.daily_challenges.find_one({"date": today}, {"_id": 0})
    if existing:
        return existing

    # Pick a subject based on day of year
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    config = DAILY_SUBJECTS[day_of_year % len(DAILY_SUBJECTS)]

    # Generate 5 questions
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"daily_{today}",
        system_message="""You are an expert educator creating a fun daily challenge.
RULES:
- Create engaging, bite-sized questions suitable for ALL grade levels
- Mix of MCQ and alphanumeric questions
- Each question should feel like a brain teaser or puzzle
- Output ONLY a JSON array — no markdown fences"""
    ).with_model("gemini", "gemini-2.0-flash")

    prompt = f"""Create 5 fun daily challenge questions for:
Subject: {config['subject']}
Topic: {config['topic']}
Difficulty: medium

For each question, include:
1. question (fun/engaging phrasing)
2. type ("mcq" or "alphanumeric")
3. options (4 options for MCQ, null for alphanumeric)
4. correct_answer
5. explanation

Return ONLY the JSON array.
"""
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        questions = json.loads(response_text.strip())

        for q in questions:
            q["id"] = str(uuid.uuid4())

    except Exception as e:
        logging.error(f"Daily challenge generation failed: {e}")
        # Fallback: pull from question bank
        cached = await db.question_bank.find({}).to_list(20)
        if cached:
            questions = random.sample(cached, min(5, len(cached)))
            for q in questions:
                q.pop("_id", None)
                q["id"] = str(uuid.uuid4())
        else:
            questions = []

    challenge = DailyChallenge(
        date=today,
        subject=config["subject"],
        topic=config["topic"],
        questions=questions
    )
    await db.daily_challenges.insert_one(challenge.model_dump())
    return challenge.model_dump()


@router.get("/challenge")
async def get_daily_challenge(current_user: User = Depends(get_current_user)):
    """Get today's daily challenge."""
    challenge = await _ensure_daily_challenge()

    # Check if user already completed it
    submission = await db.daily_submissions.find_one({
        "user_id": current_user.id,
        "date": challenge["date"]
    }, {"_id": 0})

    # Strip answers for unsolved
    if not submission:
        for q in challenge.get("questions", []):
            q.pop("correct_answer", None)
            q.pop("explanation", None)

    return {
        "challenge": challenge,
        "completed": submission is not None,
        "result": submission
    }


@router.post("/submit")
async def submit_daily_challenge(
    submission: dict,
    current_user: User = Depends(get_current_user)
):
    """Submit answers for today's daily challenge."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check if already submitted
    existing = await db.daily_submissions.find_one({
        "user_id": current_user.id, "date": today
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already completed today's challenge")

    challenge = await db.daily_challenges.find_one({"date": today}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="No challenge for today")

    # Validate answers server-side
    questions_dict = {q["id"]: q for q in challenge.get("questions", [])}
    correct_count = 0
    answers_detail = []

    for ans in submission.get("answers", []):
        question = questions_dict.get(ans.get("question_id"))
        if question:
            correct_ans = question.get("correct_answer", "").strip().upper()
            user_ans = ans.get("user_answer", "").strip().upper()
            is_correct = user_ans == correct_ans
            if is_correct:
                correct_count += 1
            answers_detail.append({
                "question_id": ans["question_id"],
                "user_answer": ans["user_answer"],
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
                "explanation": question.get("explanation", "")
            })

    total = len(challenge.get("questions", []))
    score = (correct_count / total * 100) if total > 0 else 0

    # Bonus points for daily challenge
    bonus = int(correct_count * 5 + (25 if score == 100 else 0))

    result = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "date": today,
        "score": score,
        "correct_answers": correct_count,
        "total_questions": total,
        "answers_detail": answers_detail,
        "bonus_points": bonus,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.daily_submissions.insert_one(result)

    # Award bonus points
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"points": bonus}}
    )

    return result


@router.get("/leaderboard")
async def daily_leaderboard():
    """Today's daily challenge leaderboard."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    pipeline = [
        {"$match": {"date": today}},
        {"$sort": {"score": -1, "created_at": 1}},
        {"$limit": 20}
    ]
    results = await db.daily_submissions.aggregate(pipeline).to_list(20)

    leaderboard = []
    for r in results:
        user = await db.users.find_one({"id": r["user_id"]}, {"_id": 0, "name": 1, "level": 1})
        if user:
            leaderboard.append({
                "name": user["name"],
                "level": user.get("level", 1),
                "score": r["score"],
                "time": r["created_at"]
            })

    return leaderboard
