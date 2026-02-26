"""Analytics and leaderboard routes."""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone

from db import db
from models import User
from utils.auth import get_current_user

router = APIRouter(tags=["analytics"])


@router.get("/analytics/dashboard")
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
            "avg_score": round(sum(v["scores"]) / len(v["scores"]), 1),
            "attempts": v["count"]
        }
        for v in topic_stats.values()
    ]

    # SRS stats
    srs_due = await db.srs_cards.count_documents({
        "user_id": current_user.id,
        "next_review": {"$lte": datetime.now(timezone.utc).isoformat()}
    })
    srs_total = await db.srs_cards.count_documents({"user_id": current_user.id})

    return {
        "total_quizzes": total_quizzes,
        "avg_score": round(avg_score, 1),
        "avg_focus": round(avg_focus, 1),
        "points": current_user.points,
        "level": current_user.level,
        "streak": current_user.streak,
        "badges": current_user.badges,
        "topic_performance": topic_performance,
        "recent_results": results[-5:] if len(results) > 5 else results,
        "srs_due": srs_due,
        "srs_total": srs_total
    }


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    users = await db.users.find({}, {"_id": 0, "password": 0}).sort("points", -1).limit(limit).to_list(limit)
    return users


@router.get("/leaderboard/topic/{subject}/{topic}")
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


@router.get("/subjects/active")
async def list_active_subjects():
    """Public endpoint — only active subjects."""
    return await db.subjects.find({"is_active": True}, {"_id": 0}).to_list(1000)


@router.get("/analytics/achievements")
async def get_achievements(current_user: User = Depends(get_current_user)):
    """Extended achievement data: tiered badges, milestones, streaks."""
    results = await db.quiz_results.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    total_q = len(results)
    total_correct = sum(r.get("correct_answers", 0) for r in results)
    perfect_scores = sum(1 for r in results if r.get("score", 0) == 100)
    subjects_played = list(set(r.get("subject", "") for r in results))

    # Tiered badge system
    def tier(count, bronze=1, silver=5, gold=25):
        if count >= gold:
            return "gold"
        elif count >= silver:
            return "silver"
        elif count >= bronze:
            return "bronze"
        return "locked"

    badges = [
        {"id": "quiz_warrior", "name": "Quiz Warrior", "icon": "⚔️",
         "desc": "Complete quizzes", "tier": tier(total_q, 1, 10, 50),
         "progress": total_q, "next_at": 1 if total_q < 1 else 10 if total_q < 10 else 50},
        {"id": "perfectionist", "name": "Perfectionist", "icon": "💎",
         "desc": "Get 100% scores", "tier": tier(perfect_scores, 1, 5, 20),
         "progress": perfect_scores, "next_at": 1 if perfect_scores < 1 else 5 if perfect_scores < 5 else 20},
        {"id": "knowledge_seeker", "name": "Knowledge Seeker", "icon": "📚",
         "desc": "Answer questions correctly", "tier": tier(total_correct, 10, 100, 500),
         "progress": total_correct, "next_at": 10 if total_correct < 10 else 100 if total_correct < 100 else 500},
        {"id": "explorer", "name": "Explorer", "icon": "🌍",
         "desc": "Study different subjects", "tier": tier(len(subjects_played), 2, 3, 5),
         "progress": len(subjects_played), "next_at": 2 if len(subjects_played) < 2 else 3 if len(subjects_played) < 3 else 5},
        {"id": "streak_master", "name": "Streak Master", "icon": "🔥",
         "desc": "Maintain daily streaks", "tier": tier(current_user.streak, 3, 7, 30),
         "progress": current_user.streak, "next_at": 3 if current_user.streak < 3 else 7 if current_user.streak < 7 else 30},
        {"id": "speed_demon", "name": "Speed Demon", "icon": "⚡",
         "desc": "Avg time under 10s", "tier": "gold" if any(r.get("avg_time", 99) < 10 and r.get("score", 0) >= 80 for r in results) else "locked",
         "progress": sum(1 for r in results if r.get("avg_time", 99) < 10 and r.get("score", 0) >= 80),
         "next_at": 1},
    ]

    # Milestones
    milestones = [
        {"label": "First Quiz", "reached": total_q >= 1},
        {"label": "10 Quizzes", "reached": total_q >= 10},
        {"label": "50 Quizzes", "reached": total_q >= 50},
        {"label": "100 Questions Right", "reached": total_correct >= 100},
        {"label": "500 Questions Right", "reached": total_correct >= 500},
        {"label": "7-Day Streak", "reached": current_user.streak >= 7},
        {"label": "30-Day Streak", "reached": current_user.streak >= 30},
    ]

    return {
        "badges": badges,
        "milestones": milestones,
        "total_quizzes": total_q,
        "total_correct": total_correct,
        "perfect_scores": perfect_scores,
        "subjects_played": subjects_played,
        "streak": current_user.streak,
        "level": current_user.level,
        "points": current_user.points,
    }

