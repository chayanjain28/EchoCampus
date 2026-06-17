from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database.connection import get_db
from backend.models.models import Feedback, User
from backend.schemas.schemas import FeedbackCreate, FeedbackResponse
from backend.auth.auth_handler import get_current_user, admin_required

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("/", status_code=201)
def submit_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fb = Feedback(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        category=data.category,
        rating=data.rating,
        message=data.message
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return {
        "id": fb.id,
        "organization_id": fb.organization_id,
        "user_id": fb.user_id,
        "category": fb.category,
        "rating": fb.rating,
        "message": fb.message,
        "created_at": fb.created_at,
        "student_name": current_user.name
    }


@router.get("/")
def list_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    feedbacks = db.query(Feedback).filter(
        Feedback.organization_id == current_user.organization_id
    ).order_by(Feedback.created_at.desc()).all()

    result = []
    for fb in feedbacks:
        user = db.query(User).filter(User.id == fb.user_id).first()
        result.append({
            "id": fb.id,
            "organization_id": fb.organization_id,
            "user_id": fb.user_id,
            "category": fb.category,
            "rating": fb.rating,
            "message": fb.message,
            "created_at": fb.created_at,
            "student_name": user.name if user else "Unknown"
        })
    return result
