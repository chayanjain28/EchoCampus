from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
from datetime import datetime, timezone, timedelta

from backend.database.connection import get_db
from backend.models.models import Complaint, User, Feedback, ComplaintSupport
from backend.auth.auth_handler import get_current_user, admin_required

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _get_org_id(current_user: User) -> int:
    return current_user.organization_id


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    org_id = _get_org_id(current_user)
    now = datetime.now(timezone.utc)

    # ─── Basic counts ───────────────────────────────────────────────────────
    total_complaints = db.query(func.count(Complaint.id)).filter(Complaint.organization_id == org_id).scalar() or 0
    total_students = db.query(func.count(User.id)).filter(User.organization_id == org_id, User.role == "student").scalar() or 0
    resolved = db.query(func.count(Complaint.id)).filter(Complaint.organization_id == org_id, Complaint.status == "Resolved").scalar() or 0
    pending = db.query(func.count(Complaint.id)).filter(Complaint.organization_id == org_id, Complaint.status == "Pending").scalar() or 0
    in_progress = db.query(func.count(Complaint.id)).filter(Complaint.organization_id == org_id, Complaint.status == "In Progress").scalar() or 0
    escalated = db.query(func.count(Complaint.id)).filter(Complaint.organization_id == org_id, Complaint.status == "Escalated").scalar() or 0
    total_active = pending + in_progress + escalated

    # ─── Category distribution ──────────────────────────────────────────────
    cat_rows = db.query(Complaint.category, func.count(Complaint.id)).filter(
        Complaint.organization_id == org_id
    ).group_by(Complaint.category).all()
    category_distribution = {cat: cnt for cat, cnt in cat_rows}
    most_reported = max(category_distribution, key=category_distribution.get) if category_distribution else "N/A"

    # ─── Sentiment distribution ─────────────────────────────────────────────
    sent_rows = db.query(Complaint.sentiment, func.count(Complaint.id)).filter(
        Complaint.organization_id == org_id
    ).group_by(Complaint.sentiment).all()
    sentiment_dist = {s: c for s, c in sent_rows}

    # ─── Priority distribution ──────────────────────────────────────────────
    prio_rows = db.query(Complaint.priority, func.count(Complaint.id)).filter(
        Complaint.organization_id == org_id
    ).group_by(Complaint.priority).all()
    priority_dist = {p: c for p, c in prio_rows}

    # ─── Status distribution ────────────────────────────────────────────────
    status_rows = db.query(Complaint.status, func.count(Complaint.id)).filter(
        Complaint.organization_id == org_id
    ).group_by(Complaint.status).all()
    status_dist = {s: c for s, c in status_rows}

    # ─── Monthly trend (last 6 months) ─────────────────────────────────────
    monthly_trend = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        count = db.query(func.count(Complaint.id)).filter(
            Complaint.organization_id == org_id,
            Complaint.created_at >= month_start,
            Complaint.created_at < month_end
        ).scalar() or 0
        monthly_trend.append({"month": month_start.strftime("%b %Y"), "count": count})

    # ─── CSSI (Category Service Satisfaction Index) ─────────────────────────
    categories = ["Hostel", "Mess", "WiFi", "Transport", "Academic", "Security", "Infrastructure"]
    cssi = []
    for cat in categories:
        total_cat = db.query(func.count(Complaint.id)).filter(
            Complaint.organization_id == org_id,
            Complaint.category == cat
        ).scalar() or 0
        if total_cat == 0:
            cssi.append({"category": cat, "score": 100.0})
            continue
        negative = db.query(func.count(Complaint.id)).filter(
            Complaint.organization_id == org_id,
            Complaint.category == cat,
            Complaint.sentiment == "Negative"
        ).scalar() or 0
        score = round(100.0 * (1 - negative / total_cat), 1)
        cssi.append({"category": cat, "score": score})

    # ─── Avg resolution time ────────────────────────────────────────────────
    resolved_complaints = db.query(Complaint).filter(
        Complaint.organization_id == org_id,
        Complaint.status == "Resolved",
        Complaint.resolved_at != None
    ).all()
    if resolved_complaints:
        total_hours = sum(
            (c.resolved_at - c.created_at).total_seconds() / 3600
            for c in resolved_complaints
            if c.resolved_at and c.created_at
        )
        avg_resolution_hours = round(total_hours / len(resolved_complaints), 1)
    else:
        avg_resolution_hours = 0.0

    # ─── Campus Health Score = f(resolution rate, escalation, satisfaction) ─
    resolution_rate = (resolved / total_complaints * 100) if total_complaints > 0 else 100
    escalation_penalty = (escalated / total_complaints * 100) if total_complaints > 0 else 0
    avg_feedback = db.query(func.avg(Feedback.rating)).filter(Feedback.organization_id == org_id).scalar() or 3.0
    campus_health = max(0, min(100, int(resolution_rate * 0.5 + (avg_feedback / 5.0) * 30 - escalation_penalty * 0.2)))

    # ─── Admin Efficiency Score ─────────────────────────────────────────────
    resolved_in_time = db.query(func.count(Complaint.id)).filter(
        Complaint.organization_id == org_id,
        Complaint.status == "Resolved"
    ).scalar() or 0
    admin_efficiency = int((resolved_in_time / total_complaints * 100)) if total_complaints > 0 else 100

    # ─── Student Satisfaction Index ─────────────────────────────────────────
    feedback_avg = round(float(avg_feedback), 2)

    # ─── Most supported issue ───────────────────────────────────────────────
    top_support = db.query(Complaint.title, func.count(ComplaintSupport.id).label("support_count")).join(
        ComplaintSupport, ComplaintSupport.complaint_id == Complaint.id
    ).filter(Complaint.organization_id == org_id).group_by(Complaint.id).order_by(func.count(ComplaintSupport.id).desc()).first()
    most_supported = top_support.title if top_support else None

    # ─── Duplicate groups ───────────────────────────────────────────────────
    duplicate_groups = db.query(func.count(Complaint.id)).filter(
        Complaint.organization_id == org_id,
        Complaint.parent_complaint_id != None
    ).scalar() or 0

    # ─── Total affected students (unique supporters + original reporters) ───
    total_supports = db.query(func.count(ComplaintSupport.id)).filter(
        ComplaintSupport.organization_id == org_id
    ).scalar() or 0

    # ─── Department workload ────────────────────────────────────────────────
    dept_rows = db.query(Complaint.assigned_department, func.count(Complaint.id)).filter(
        Complaint.organization_id == org_id
    ).group_by(Complaint.assigned_department).all()
    dept_workload = [{"department": d, "count": c} for d, c in dept_rows]

    # ─── Recent high-impact ─────────────────────────────────────────────────
    high_impact = db.query(Complaint).filter(
        Complaint.organization_id == org_id,
        Complaint.status != "Resolved"
    ).order_by(Complaint.impact_score.desc()).limit(5).all()
    high_impact_list = [{"id": c.id, "title": c.title, "impact_score": c.impact_score, "priority": c.priority, "category": c.category} for c in high_impact]

    return {
        "campus_health_score": campus_health,
        "student_satisfaction_index": feedback_avg,
        "admin_efficiency_score": admin_efficiency,
        "avg_resolution_time_hours": avg_resolution_hours,
        "total_complaints": total_complaints,
        "total_students": total_students,
        "resolved_complaints": resolved,
        "pending_complaints": pending,
        "escalated_complaints_count": escalated,
        "total_active_issues": total_active,
        "most_reported_service": most_reported,
        "most_supported_issue": most_supported,
        "total_affected_students": total_supports,
        "duplicate_groups_count": duplicate_groups,
        "resolution_rate": round(resolution_rate, 1),
        "category_distribution": category_distribution,
        "sentiment_distribution": sentiment_dist,
        "priority_distribution": priority_dist,
        "status_distribution": status_dist,
        "monthly_trend": monthly_trend,
        "cssi": cssi,
        "department_workload": dept_workload,
        "high_impact_issues": high_impact_list,
    }


@router.get("/student")
def student_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analytics for the student's own activity within the org."""
    org_id = current_user.organization_id
    uid = current_user.id

    my_total = db.query(func.count(Complaint.id)).filter(Complaint.user_id == uid).scalar() or 0
    my_resolved = db.query(func.count(Complaint.id)).filter(Complaint.user_id == uid, Complaint.status == "Resolved").scalar() or 0
    my_pending = db.query(func.count(Complaint.id)).filter(Complaint.user_id == uid, Complaint.status == "Pending").scalar() or 0
    my_supported = db.query(func.count(ComplaintSupport.id)).filter(ComplaintSupport.user_id == uid).scalar() or 0

    recent = db.query(Complaint).filter(Complaint.user_id == uid).order_by(Complaint.created_at.desc()).limit(5).all()
    recent_list = [{"id": c.id, "title": c.title, "status": c.status, "priority": c.priority, "category": c.category, "created_at": c.created_at} for c in recent]

    org_total = db.query(func.count(Complaint.id)).filter(Complaint.organization_id == org_id).scalar() or 1
    org_sentiment = db.query(Complaint.sentiment, func.count(Complaint.id)).filter(
        Complaint.organization_id == org_id
    ).group_by(Complaint.sentiment).all()
    org_sentiment_dict = {s: c for s, c in org_sentiment}

    return {
        "my_complaints": my_total,
        "my_resolved": my_resolved,
        "my_pending": my_pending,
        "my_supported_issues": my_supported,
        "recent_complaints": recent_list,
        "org_sentiment_distribution": org_sentiment_dict,
        "org_resolution_rate": round(
            db.query(func.count(Complaint.id)).filter(Complaint.organization_id == org_id, Complaint.status == "Resolved").scalar() / org_total * 100, 1
        ),
    }
