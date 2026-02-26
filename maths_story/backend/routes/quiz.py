"""Quiz generation and submission routes — with story mode, timed/untimed, SRS integration."""
from fastapi import APIRouter, HTTPException, Depends
from emergentintegrations.llm.chat import LlmChat, UserMessage
from datetime import datetime, timezone, timedelta
import json
import uuid
import re
import asyncio
import logging
import os
import random

from db import db, UPLOAD_DIR
from models import User, Quiz, QuizRequest, QuizSubmission, QuizResult, SRSCard
from utils.auth import get_current_user
from utils.pdf import extract_text_from_pdf

router = APIRouter(prefix="/quiz", tags=["quiz"])

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')


# ============ Helpers ============

async def _build_context(request: QuizRequest) -> str:
    """Build knowledge-base context from cached text and chunks."""
    context_text = ""
    if not request.subtopic:
        return context_text

    # Try cached extracted_text first
    subtopic = await db.subtopics.find_one(
        {"name": request.subtopic, "knowledge_base_files": {"$exists": True, "$ne": []}},
        {"_id": 0}
    )
    if subtopic and subtopic.get("extracted_text"):
        context_text = subtopic["extracted_text"]
    elif subtopic and subtopic.get("knowledge_base_files"):
        # Fallback: parallel extraction
        async def _extract(filepath):
            content = await asyncio.to_thread(lambda: open(filepath, "rb").read())
            return await asyncio.to_thread(extract_text_from_pdf, content)

        tasks = []
        for pdf_file in subtopic["knowledge_base_files"][:3]:
            fp = UPLOAD_DIR / pdf_file
            if fp.exists():
                tasks.append(_extract(fp))
        if tasks:
            texts = await asyncio.gather(*tasks)
            context_text = "\n\n".join(t[:3000] for t in texts if t)

    # Keyword-based chunk selection (better relevance)
    chunks = await db.knowledge_chunks.find(
        {"subtopic_name": request.subtopic}
    ).to_list(200)
    if chunks:
        keywords = set(re.findall(r'\w+', (request.topic + " " + (request.subtopic or "")).lower()))
        scored = []
        for chunk in chunks:
            words = set(re.findall(r'\w+', chunk["content"].lower()))
            overlap = len(keywords & words)
            scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[:5]
        context_text = "\n\n".join(c["content"] for _, c in best)

    return context_text


async def _get_weak_areas(user_id: str, subject: str, current_topic: str) -> str:
    """Check student weak areas for adaptive quizzing."""
    weak_results = await db.quiz_results.find({
        "user_id": user_id,
        "subject": subject,
        "score": {"$lt": 60}
    }).sort("created_at", -1).limit(5).to_list(5)
    if weak_results:
        weak_topics = list(set(r.get("topic", "") for r in weak_results if r.get("topic") != current_topic))
        if weak_topics:
            return f"\nThis student previously struggled with: {', '.join(weak_topics[:3])}.\nInclude 1 review question touching on those weak areas if relevant.\n"
    return ""


def _build_system_message(story_mode: bool = False, mode: str = "timed") -> str:
    """Build the system message for the LLM."""
    base = """You are an expert K-12 educator who creates quiz questions.

RULES:
- Questions must directly test concepts from the provided context when available
- MCQ distractors must be plausible (common student errors, not obviously wrong)
- Explanations should TEACH the concept, not just state the answer
- For alphanumeric: the correct_answer should be the simplest form
- Match language complexity to the specified grade level
- Output ONLY a JSON array — no markdown fences, no extra text"""

    if story_mode:
        base += """

STORY MODE — IMPORTANT:
- Weave ALL questions into a single continuous, engaging narrative/story
- Use a relatable character (give them a name!) and a fun scenario (space adventure, cooking competition, building a fort, etc.)
- Each question should advance the story — the student is helping the character solve problems
- Make it age-appropriate, fun, and immersive
- Add a "story_context" field to each question with 1-2 sentences of narrative that sets up the problem"""

    if mode == "practice":
        base += """

PRACTICE MODE:
- Include a "hint" field for each question (a helpful nudge without giving away the answer)
- Explanations should be extra detailed with step-by-step solutions
- Make questions slightly easier to build confidence"""

    elif mode == "exam":
        base += """

EXAM PREP MODE:
- Questions should mimic real exam format (competitive exams, board exams)
- No hints allowed
- Higher rigor — test application, not just recall
- Include "difficulty_rating" field: 1 (easy), 2 (medium), 3 (hard)"""

    return base


def _build_prompt(request: QuizRequest, context_text: str, weak_hint: str) -> str:
    """Build the user prompt."""
    context_instruction = ""
    if context_text:
        context_instruction = f"\n\nKNOWLEDGE BASE CONTEXT (base questions on this):\n{context_text[:6000]}\n"

    grade_instruction = ""
    if request.grade:
        grade_instruction = f"\nGrade Level: {request.grade}\nAdjust complexity to suit {request.grade} students.\n"

    story_fields = ""
    if request.story_mode:
        story_fields = '\n6. story_context (1-2 sentences of narrative before the question)'
    
    hint_field = ""
    if request.mode == "practice":
        hint_field = '\n7. hint (a helpful nudge without giving the answer)'
    
    difficulty_field = ""
    if request.mode == "exam":
        difficulty_field = '\n7. difficulty_rating (1=easy, 2=medium, 3=hard)'

    return f"""Create {request.num_questions} quiz questions for:
Subject: {request.subject}
Topic: {request.topic}
{f'Subtopic: {request.subtopic}' if request.subtopic else ''}
{f'Grade: {request.grade}' if request.grade else ''}
Difficulty: {request.difficulty}
{context_instruction}
{grade_instruction}
{weak_hint}
For each question, include:
1. question text
2. type ("mcq" or "alphanumeric")
3. options (array of 4 options for MCQ, null for alphanumeric)
4. correct_answer (option letter like "A" for MCQ, actual answer for alphanumeric)
5. explanation (2-3 sentences teaching the concept){story_fields}{hint_field}{difficulty_field}

EXAMPLE OUTPUT:
[
  {{
    "question": "If x² + 5x + 6 = 0, what are the values of x?",
    "type": "mcq",
    "options": ["A. x = -2 and x = -3", "B. x = 2 and x = 3", "C. x = -1 and x = -6", "D. x = 1 and x = 6"],
    "correct_answer": "A",
    "explanation": "Factor the quadratic: (x+2)(x+3) = 0. Setting each factor to zero gives x = -2 or x = -3."
  }}
]

Return ONLY the JSON array for {request.num_questions} questions.
"""


async def _generate_questions(request: QuizRequest, context_text: str, weak_hint: str) -> list:
    """Generate questions with 3-attempt retry and question bank fallback."""
    system_msg = _build_system_message(request.story_mode, request.mode)
    prompt = _build_prompt(request, context_text, weak_hint)

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"quiz_{uuid.uuid4()}",
        system_message=system_msg
    ).with_model("gemini", "gemini-2.0-flash")

    questions_data = None
    last_error = None
    for attempt in range(3):
        try:
            retry_hint = ""
            if attempt > 0:
                retry_hint = "\n\nIMPORTANT: Your previous response had invalid JSON. Return ONLY a valid JSON array, nothing else."
            user_message = UserMessage(text=prompt + retry_hint)
            response = await chat.send_message(user_message)

            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            questions_data = json.loads(response_text)

            if not isinstance(questions_data, list) or len(questions_data) == 0:
                raise ValueError("Response is not a non-empty JSON array")
            for q in questions_data:
                if "question" not in q or "correct_answer" not in q:
                    raise ValueError("Missing required fields in question")
            break
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            logging.warning(f"Quiz generation attempt {attempt + 1} failed: {str(e)}")
            if attempt == 2:
                # Fallback: question bank
                cached = await db.question_bank.find({
                    "subject": request.subject,
                    "topic": request.topic,
                    "difficulty": request.difficulty
                }).to_list(request.num_questions * 2)
                if len(cached) >= request.num_questions:
                    questions_data = random.sample(cached, request.num_questions)
                    for q in questions_data:
                        q.pop("_id", None)
                        q.pop("times_served", None)
                        q.pop("times_correct", None)
                    logging.info("Serving quiz from question bank fallback")
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to generate quiz after 3 attempts: {str(last_error)}")

    return questions_data


# ============ Endpoints ============

@router.post("/generate")
async def generate_quiz(request: QuizRequest, current_user: User = Depends(get_current_user)):
    # Rate limiting: 20/hour
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    recent_count = await db.quizzes.count_documents({
        "user_id": current_user.id,
        "created_at": {"$gte": one_hour_ago}
    })
    if recent_count >= 20:
        raise HTTPException(status_code=429, detail="Quiz generation limit reached (20/hour). Try again later.")

    try:
        context_text = await _build_context(request)
        weak_hint = await _get_weak_areas(current_user.id, request.subject, request.topic)
        questions_data = await _generate_questions(request, context_text, weak_hint)

        # Add IDs
        for q in questions_data:
            q["id"] = str(uuid.uuid4())

        quiz = Quiz(
            user_id=current_user.id,
            subject=request.subject,
            topic=request.topic,
            subtopic=request.subtopic,
            difficulty=request.difficulty,
            mode=request.mode,
            story_mode=request.story_mode,
            questions=questions_data
        )
        await db.quizzes.insert_one(quiz.model_dump())

        # Save to question bank
        for q in questions_data:
            q_bank = {
                **q,
                "subject": request.subject,
                "topic": request.topic,
                "subtopic": request.subtopic,
                "grade": request.grade,
                "difficulty": request.difficulty,
                "source": "llm",
                "times_served": 1,
                "times_correct": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.question_bank.update_one(
                {"question": q["question"], "subject": request.subject},
                {"$setOnInsert": q_bank},
                upsert=True
            )

        # Return without correct answers
        quiz_response = quiz.model_dump()
        for q in quiz_response["questions"]:
            q.pop("correct_answer", None)
            q.pop("explanation", None)

        return quiz_response

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Quiz generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.post("/submit")
async def submit_quiz(submission: QuizSubmission, current_user: User = Depends(get_current_user)):
    quiz = await db.quizzes.find_one({"id": submission.quiz_id}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Server-side answer validation
    correct_count = 0
    total_time = 0
    time_variance = []
    answers_detail = []

    questions_dict = {q["id"]: q for q in quiz["questions"]}

    for answer in submission.answers:
        question = questions_dict.get(answer.question_id)
        if question:
            correct_ans = question.get("correct_answer", "").strip().upper()
            user_ans = answer.user_answer.strip().upper()
            is_correct = user_ans == correct_ans

            if is_correct:
                correct_count += 1
                await db.question_bank.update_one(
                    {"question": question["question"]},
                    {"$inc": {"times_served": 1, "times_correct": 1}}
                )
            else:
                await db.question_bank.update_one(
                    {"question": question["question"]},
                    {"$inc": {"times_served": 1}}
                )
                # Add to SRS for wrong answers
                existing_card = await db.srs_cards.find_one({
                    "user_id": current_user.id,
                    "question.question": question["question"]
                })
                if not existing_card:
                    card = SRSCard(
                        user_id=current_user.id,
                        question=question,
                        subject=quiz["subject"],
                        topic=quiz["topic"],
                        bucket=0,
                        next_review=datetime.now(timezone.utc).isoformat()
                    )
                    await db.srs_cards.insert_one(card.model_dump())

            answers_detail.append({
                "question_id": answer.question_id,
                "question": question["question"],
                "user_answer": answer.user_answer,
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
                "time_taken": answer.time_taken,
                "explanation": question.get("explanation", ""),
                "hint": question.get("hint", ""),
                "story_context": question.get("story_context", "")
            })

        total_time += answer.time_taken
        time_variance.append(answer.time_taken)

    avg_time = total_time / len(submission.answers) if submission.answers else 0

    # Focus score
    if len(time_variance) > 1:
        variance = sum((t - avg_time) ** 2 for t in time_variance) / len(time_variance)
        focus_score = max(0, min(100, 100 - (variance / 10)))
    else:
        focus_score = 80

    score = (correct_count / len(submission.answers)) * 100 if submission.answers else 0
    points_earned = int(correct_count * 10 + focus_score / 10)

    # Streak
    today = datetime.now(timezone.utc).date().isoformat()
    last_activity = current_user.last_activity
    streak_update = {}
    if last_activity:
        try:
            last_date = datetime.fromisoformat(last_activity).date()
            today_date = datetime.now(timezone.utc).date()
            if (today_date - last_date).days == 1:
                streak_update = {"$inc": {"streak": 1}}
            elif (today_date - last_date).days > 1:
                streak_update = {"$set": {"streak": 1}}
        except (ValueError, TypeError):
            streak_update = {"$set": {"streak": 1}}
    else:
        streak_update = {"$set": {"streak": 1}}

    await db.users.update_one(
        {"id": current_user.id},
        {
            "$inc": {"points": points_earned},
            "$set": {"last_activity": datetime.now(timezone.utc).isoformat()},
        }
    )
    if "$inc" in streak_update:
        await db.users.update_one({"id": current_user.id}, streak_update)
    elif "$set" in streak_update:
        await db.users.update_one({"id": current_user.id}, {"$set": {"streak": streak_update["$set"]["streak"]}})

    # Level + badges
    updated_user = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    new_level = (updated_user["points"] // 100) + 1

    new_badges = list(updated_user.get("badges", []))
    total_quizzes = await db.quiz_results.count_documents({"user_id": current_user.id})
    if total_quizzes == 0 and "first_quiz" not in new_badges:
        new_badges.append("first_quiz")
    if score == 100 and "perfect_score" not in new_badges:
        new_badges.append("perfect_score")
    if updated_user.get("streak", 0) >= 7 and "week_streak" not in new_badges:
        new_badges.append("week_streak")
    if new_level >= 10 and "level_10" not in new_badges:
        new_badges.append("level_10")
    perfect_count = await db.quiz_results.count_documents({"user_id": current_user.id, "score": 100})
    if perfect_count >= 10 and "ten_perfects" not in new_badges:
        new_badges.append("ten_perfects")

    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"level": new_level, "badges": new_badges}}
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
        points_earned=points_earned,
        answers_detail=answers_detail
    )
    await db.quiz_results.insert_one(result.model_dump())

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


@router.get("/history")
async def quiz_history(
    subject: str = None,
    topic: str = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Filterable, paginated quiz history with trend data."""
    query = {"user_id": current_user.id}
    if subject:
        query["subject"] = subject
    if topic:
        query["topic"] = topic

    total = await db.quiz_results.count_documents(query)
    results = await db.quiz_results.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)

    # Score trend (last 20 results)
    trend_results = await db.quiz_results.find(
        {"user_id": current_user.id}, {"_id": 0, "score": 1, "created_at": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    trend = [{"date": r["created_at"][:10], "score": r["score"]} for r in reversed(trend_results)]

    return {
        "total": total,
        "results": results,
        "trend": trend,
        "offset": offset,
        "limit": limit
    }


@router.get("/result/{result_id}")
async def get_quiz_result(result_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed quiz result with per-question breakdown."""
    result = await db.quiz_results.find_one({"id": result_id, "user_id": current_user.id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # Also fetch original quiz questions for full review
    quiz = await db.quizzes.find_one({"id": result["quiz_id"]}, {"_id": 0})
    if quiz:
        result["questions"] = quiz["questions"]

    return result


@router.get("/share/{result_id}")
async def get_shareable_result(result_id: str):
    """Public shareable quiz result card data."""
    result = await db.quiz_results.find_one({"id": result_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    user = await db.users.find_one({"id": result["user_id"]}, {"_id": 0, "password": 0})

    return {
        "student_name": user["name"] if user else "Student",
        "subject": result["subject"],
        "topic": result["topic"],
        "score": result["score"],
        "total_questions": result["total_questions"],
        "correct_answers": result["correct_answers"],
        "focus_score": result["focus_score"],
        "date": result["created_at"][:10]
    }
