"""Spaced Repetition System (SRS) routes — Leitner box algorithm."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import logging

from db import db
from models import User
from utils.auth import get_current_user

router = APIRouter(prefix="/srs", tags=["srs"])

# Leitner intervals: bucket → days until next review
LEITNER_INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14}


@router.get("/review")
async def get_review_queue(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get cards due for review (Leitner SRS)."""
    now = datetime.now(timezone.utc).isoformat()

    cards = await db.srs_cards.find({
        "user_id": current_user.id,
        "next_review": {"$lte": now}
    }, {"_id": 0}).sort("next_review", 1).limit(limit).to_list(limit)

    # Strip answers from questions for review
    for card in cards:
        q = card.get("question", {})
        q.pop("correct_answer", None)
        q.pop("explanation", None)

    total_due = await db.srs_cards.count_documents({
        "user_id": current_user.id,
        "next_review": {"$lte": now}
    })
    total_cards = await db.srs_cards.count_documents({"user_id": current_user.id})

    return {
        "cards": cards,
        "due_count": total_due,
        "total_cards": total_cards
    }


@router.post("/review/{card_id}")
async def review_card(
    card_id: str,
    body: dict,
    current_user: User = Depends(get_current_user)
):
    """Submit a review for an SRS card. Body: { "user_answer": "...", "time_taken": 5.0 }"""
    card = await db.srs_cards.find_one({
        "id": card_id,
        "user_id": current_user.id
    }, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Validate answer server-side
    correct_ans = card["question"].get("correct_answer", "").strip().upper()
    user_ans = body.get("user_answer", "").strip().upper()
    is_correct = user_ans == correct_ans

    current_bucket = card.get("bucket", 0)
    if is_correct:
        # Move up a bucket (max 4)
        new_bucket = min(current_bucket + 1, 4)
    else:
        # Reset to bucket 0
        new_bucket = 0

    # Calculate next review date
    interval_days = LEITNER_INTERVALS.get(new_bucket, 14)
    next_review = (datetime.now(timezone.utc) + timedelta(days=interval_days)).isoformat()

    await db.srs_cards.update_one(
        {"id": card_id},
        {"$set": {
            "bucket": new_bucket,
            "next_review": next_review,
        },
        "$inc": {
            "times_reviewed": 1,
            "times_correct": 1 if is_correct else 0
        }}
    )

    # Bonus points for SRS review
    points = 3 if is_correct else 1
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"points": points}}
    )

    return {
        "is_correct": is_correct,
        "correct_answer": card["question"]["correct_answer"],
        "explanation": card["question"].get("explanation", ""),
        "new_bucket": new_bucket,
        "next_review": next_review,
        "points_earned": points
    }


@router.get("/stats")
async def srs_stats(current_user: User = Depends(get_current_user)):
    """Get SRS statistics."""
    now = datetime.now(timezone.utc).isoformat()

    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {
            "_id": "$bucket",
            "count": {"$sum": 1}
        }}
    ]
    bucket_stats = await db.srs_cards.aggregate(pipeline).to_list(10)
    buckets = {str(b["_id"]): b["count"] for b in bucket_stats}

    total = await db.srs_cards.count_documents({"user_id": current_user.id})
    due = await db.srs_cards.count_documents({
        "user_id": current_user.id,
        "next_review": {"$lte": now}
    })
    mastered = await db.srs_cards.count_documents({
        "user_id": current_user.id,
        "bucket": {"$gte": 4}
    })

    return {
        "total_cards": total,
        "due_now": due,
        "mastered": mastered,
        "bucket_distribution": buckets
    }


@router.delete("/card/{card_id}")
async def delete_card(card_id: str, current_user: User = Depends(get_current_user)):
    """Remove a card from SRS."""
    result = await db.srs_cards.delete_one({"id": card_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"message": "Card removed from review"}
