from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timezone
import shutil, os

from backend.database.connection import get_db
from backend.models.models import Complaint, User, Notification, ComplaintSupport
from backend.schemas.schemas import ComplaintCreate, ComplaintDetailResponse, ComplaintStatusUpdate, ResolutionRate
from backend.auth.auth_handler import get_current_user, admin_required, moderator_required
from backend.services.gemini_service import analyze_complaint

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DEPARTMENT_MAP = {
    "WiFi": "IT Department",
    "Hostel": "Hostel Warden",
    "Mess": "Mess Committee",
    "Transport": "Transport Office",
    "Academic": "Academic Cell",
    "Security": "Security Office",
    "Infrastructure": "Maintenance Department",
    "Other": "General Administration"
}

def _complaint_response(c: Complaint, current_user: User, db: Session) -> dict:
    support_count = db.query(func.count(ComplaintSupport.id)).filter(
        ComplaintSupport.complaint_id == c.id
    ).scalar() or 0
    user_supported = db.query(ComplaintSupport).filter(
        ComplaintSupport.complaint_id == c.id,
        ComplaintSupport.user_id == current_user.id
    ).first() is not None
    duplicate_count = db.query(func.count(Complaint.id)).filter(
        Complaint.parent_complaint_id == c.id,
        Complaint.organization_id == c.organization_id
    ).scalar() or 0

    student_name = "Anonymous"
    if not c.anonymous:
        user = db.query(User).filter(User.id == c.user_id).first()
        student_name = user.name if user else "Unknown"

    return {
        "id": c.id,
        "organization_id": c.organization_id,
        "user_id": c.user_id,
        "title": c.title,
        "description": c.description,
        "category": c.category,
        "sentiment": c.sentiment,
        "priority": c.priority,
        "severity_score": c.severity_score,
        "impact_score": c.impact_score,
        "status": c.status,
        "image_path": c.image_path,
        "anonymous": c.anonymous,
        "assigned_department": c.assigned_department,
        "assigned_to": c.assigned_to,
        "duplicate_score": c.duplicate_score,
        "parent_complaint_id": c.parent_complaint_id,
        "ai_recommendation": c.ai_recommendation,
        "resolution_rating": c.resolution_rating,
        "resolution_comment": c.resolution_comment,
        "resolved_at": c.resolved_at,
        "created_at": c.created_at,
        "student_name": student_name,
        "duplicate_count": duplicate_count,
        "support_count": support_count,
        "user_has_supported": user_supported,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # AI Analysis
    try:
        ai_result = analyze_complaint(data.title, data.description)
    except Exception:
        ai_result = {
            "category": "Other",
            "sentiment": "Neutral",
            "priority": "Medium",
            "severity_score": 50,
            "assigned_department": "General Administration",
            "ai_recommendation": "Please review this complaint manually.",
            "duplicate_score": None
        }

    # Department routing
    dept = ai_result.get("assigned_department") or DEPARTMENT_MAP.get(ai_result.get("category", "Other"), "General Administration")
    severity = ai_result.get("severity_score", 50)

    # Check for similar pending complaint (naive dedup by title similarity)
    parent_id = None
    similar = db.query(Complaint).filter(
        Complaint.organization_id == current_user.organization_id,
        Complaint.category == ai_result.get("category", "Other"),
        Complaint.status != "Resolved"
    ).order_by(Complaint.created_at.desc()).first()

    # Calculate impact score = (severity * 0.6) + (support_count * 0.4)
    impact_score = round(severity * 0.6, 2)

    complaint = Complaint(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        category=ai_result.get("category", "Other"),
        sentiment=ai_result.get("sentiment", "Neutral"),
        priority=ai_result.get("priority", "Medium"),
        severity_score=severity,
        impact_score=impact_score,
        status="Pending",
        image_path=data.image_path,
        anonymous=data.anonymous,
        assigned_department=dept,
        ai_recommendation=ai_result.get("ai_recommendation", ""),
        duplicate_score=ai_result.get("duplicate_score"),
        parent_complaint_id=parent_id
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return _complaint_response(complaint, current_user, db)


@router.get("/", response_model=List[dict])
def list_complaints(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Students see only their own complaints; admins/moderators see all within org."""
    q = db.query(Complaint).filter(Complaint.organization_id == current_user.organization_id)
    if current_user.role == "student":
        q = q.filter(Complaint.user_id == current_user.id)
    if status:
        q = q.filter(Complaint.status == status)
    if category:
        q = q.filter(Complaint.category == category)
    if priority:
        q = q.filter(Complaint.priority == priority)
    if search:
        q = q.filter(Complaint.title.ilike(f"%{search}%"))

    total = q.count()
    complaints = q.order_by(Complaint.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return [_complaint_response(c, current_user, db) for c in complaints]


@router.get("/all", response_model=List[dict])
def list_all_complaints_admin(
    status_filter: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(moderator_required)
):
    """Admin/Moderator sees all complaints in their workspace."""
    q = db.query(Complaint).filter(Complaint.organization_id == current_user.organization_id)
    if status_filter:
        q = q.filter(Complaint.status == status_filter)
    if category:
        q = q.filter(Complaint.category == category)
    if priority:
        q = q.filter(Complaint.priority == priority)
    if search:
        q = q.filter(Complaint.title.ilike(f"%{search}%"))
    if department:
        q = q.filter(Complaint.assigned_department == department)

    complaints = q.order_by(Complaint.impact_score.desc(), Complaint.created_at.desc()).all()
    return [_complaint_response(c, current_user, db) for c in complaints]


@router.get("/{complaint_id}")
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    c = db.query(Complaint).filter(
        Complaint.id == complaint_id,
        Complaint.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if current_user.role == "student" and c.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _complaint_response(c, current_user, db)


@router.put("/{complaint_id}/status")
def update_status(
    complaint_id: int,
    data: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(moderator_required)
):
    c = db.query(Complaint).filter(
        Complaint.id == complaint_id,
        Complaint.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    c.status = data.status
    if data.assigned_to:
        c.assigned_to = data.assigned_to
    if data.assigned_department:
        c.assigned_department = data.assigned_department
    if data.status == "Resolved":
        c.resolved_at = datetime.now(timezone.utc)

    # Notify student
    notif = Notification(
        organization_id=c.organization_id,
        user_id=c.user_id,
        message=f"Your complaint '{c.title}' status has been updated to: {data.status}"
    )
    db.add(notif)
    db.commit()
    db.refresh(c)
    return _complaint_response(c, current_user, db)


@router.post("/{complaint_id}/support")
def toggle_support(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """'I Am Also Affected' – students can support complaints they relate to."""
    c = db.query(Complaint).filter(
        Complaint.id == complaint_id,
        Complaint.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    existing = db.query(ComplaintSupport).filter(
        ComplaintSupport.complaint_id == complaint_id,
        ComplaintSupport.user_id == current_user.id
    ).first()

    if existing:
        # Remove support (toggle off)
        db.delete(existing)
        db.commit()
        action = "removed"
    else:
        # Add support
        support = ComplaintSupport(
            organization_id=current_user.organization_id,
            complaint_id=complaint_id,
            user_id=current_user.id
        )
        db.add(support)
        db.commit()
        action = "added"

    # Recalculate impact score after support change
    support_count = db.query(func.count(ComplaintSupport.id)).filter(
        ComplaintSupport.complaint_id == complaint_id
    ).scalar() or 0
    c.impact_score = round((c.severity_score * 0.6) + (support_count * 0.4), 2)
    db.commit()

    return {"action": action, "support_count": support_count, "impact_score": c.impact_score}


@router.post("/{complaint_id}/rate")
def rate_resolution(
    complaint_id: int,
    data: ResolutionRate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    c = db.query(Complaint).filter(
        Complaint.id == complaint_id,
        Complaint.organization_id == current_user.organization_id,
        Complaint.user_id == current_user.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found or not yours")
    if c.status != "Resolved":
        raise HTTPException(status_code=400, detail="Can only rate resolved complaints")
    c.resolution_rating = data.rating
    c.resolution_comment = data.comment
    db.commit()
    return {"message": "Rating submitted successfully"}


@router.post("/upload-image")
def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    filename = f"{current_user.id}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"image_path": f"/uploads/{filename}"}


@router.delete("/{complaint_id}")
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    c = db.query(Complaint).filter(
        Complaint.id == complaint_id,
        Complaint.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    db.delete(c)
    db.commit()
    return {"message": "Complaint deleted"}
