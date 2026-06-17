"""
Multi-Tenant Seed Script for EchoCampus AI V2.0
Creates two isolated demo organizations with full sample data.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import SessionLocal, engine, Base
from backend.models.models import Organization, User, Complaint, Feedback, Notification, ComplaintSupport
from backend.utils.security import hash_password
from datetime import datetime, timezone, timedelta
import random

Base.metadata.create_all(bind=engine)
db = SessionLocal()

CATEGORIES    = ["Hostel", "Mess", "WiFi", "Transport", "Academic", "Infrastructure", "Security", "Other"]
SENTIMENTS    = ["Positive", "Neutral", "Negative"]
PRIORITIES    = ["Low", "Medium", "High", "Critical"]
STATUSES      = ["Pending", "In Progress", "Resolved", "Escalated"]
DEPT_MAP      = {
    "WiFi": "IT Department", "Hostel": "Hostel Warden", "Mess": "Mess Committee",
    "Transport": "Transport Office", "Academic": "Academic Cell",
    "Security": "Security Office", "Infrastructure": "Maintenance Department",
    "Other": "General Administration"
}

COMPLAINT_SAMPLES = [
    ("WiFi keeps disconnecting in Block A", "The WiFi in Hostel Block A disconnects every 30 minutes. It's impossible to attend online classes.", "WiFi", "Negative", "High", 72),
    ("Mess food quality has severely declined", "The food served in the mess has deteriorated. Rice is undercooked and vegetables are stale.", "Mess", "Negative", "High", 78),
    ("Room heater not working in winter", "The heater in room 204 has been broken since December. Nights are freezing cold.", "Hostel", "Negative", "Critical", 88),
    ("Bus Route 3 always arrives late", "The college bus on Route 3 arrives 25-30 minutes late every single day. Students miss morning classes.", "Transport", "Negative", "Medium", 55),
    ("Unfair internal marks allocation", "Internal marks were given without proper evaluation criteria. Several students received marks without appearing for tests.", "Academic", "Negative", "High", 70),
    ("Broken street lights near girls hostel", "The street lights near Girls Hostel B have been non-functional for 2 weeks. Security risk at night.", "Security", "Negative", "Critical", 92),
    ("Water supply disruption - Hostel C", "Water supply to Hostel C has been disrupted since Monday. Students cannot bathe or wash utensils.", "Infrastructure", "Negative", "Critical", 90),
    ("Library AC not working", "The air conditioning in the library reading room stopped working. It's very hot and students cannot study.", "Infrastructure", "Negative", "Medium", 58),
    ("Sports ground not maintained", "The cricket ground has not been maintained. The pitch is uneven and dangerous to play on.", "Other", "Neutral", "Low", 25),
    ("WiFi password changed without notice", "The WiFi password was changed without informing students. We lost access for 2 days during exam week.", "WiFi", "Negative", "High", 68),
    ("Unhygienic kitchen conditions in mess", "Cockroaches were spotted near the mess kitchen. This is a serious health hazard.", "Mess", "Negative", "Critical", 95),
    ("Professor frequently cancels classes", "The Data Structures professor has cancelled 8 consecutive classes without prior notice or make-up sessions.", "Academic", "Negative", "High", 75),
    ("New timetable issued very late", "The revised exam timetable was issued only 3 days before exams began leaving no time to prepare.", "Academic", "Neutral", "Medium", 42),
    ("Good response from maintenance team", "The maintenance team fixed our plumbing issue within hours. Really appreciate the quick response!", "Hostel", "Positive", "Low", 10),
    ("Request for additional study rooms", "The library closes at 9 PM but students need late-night study facilities, especially during exam season.", "Infrastructure", "Neutral", "Medium", 45),
    ("Security guard behaved rudely", "The guard at the main gate was rude when I asked for help. The behavior was unprofessional.", "Security", "Negative", "Medium", 55),
    ("Mess timings too short on weekends", "On weekends, the mess only stays open for 45 minutes for lunch. Many students miss meals.", "Mess", "Negative", "Medium", 60),
    ("Projector in Lab 3 is broken", "The projector in Computer Lab 3 has been broken for over a month. Lectures cannot be conducted properly.", "Infrastructure", "Neutral", "High", 65),
]

def create_org_data(
    org_name: str, org_type: str, workspace_code: str, invite_code: str,
    admin_name: str, admin_email: str,
    students: list   # [(name, email)]
):
    # Create organization
    org = Organization(
        name=org_name, type=org_type,
        workspace_code=workspace_code, invite_code=invite_code,
        description=f"Demo workspace for {org_name}",
        logo_url=None
    )
    db.add(org)
    db.flush()

    # Admin user
    admin = User(
        organization_id=org.id, name=admin_name, email=admin_email,
        password_hash=hash_password("Admin@123"), role="admin"
    )
    db.add(admin)
    db.flush()

    # Student users
    user_objects = []
    for name, email in students:
        u = User(
            organization_id=org.id, name=name, email=email,
            password_hash=hash_password("Student@123"), role="student"
        )
        db.add(u)
        db.flush()
        user_objects.append(u)

    # Complaints (18 samples, distributed)
    complaint_objects = []
    now = datetime.now(timezone.utc)
    for i, sample in enumerate(COMPLAINT_SAMPLES):
        title, desc, cat, sentiment, priority, severity = sample
        student = user_objects[i % len(user_objects)]
        days_ago = random.randint(1, 45)
        created = now - timedelta(days=days_ago)
        status = random.choice(STATUSES)
        resolved_at = (created + timedelta(days=random.randint(1, 5))) if status == "Resolved" else None
        impact = round(severity * 0.6, 2)

        c = Complaint(
            organization_id=org.id, user_id=student.id,
            title=title, description=desc,
            category=cat, sentiment=sentiment,
            priority=priority, severity_score=severity,
            impact_score=impact, status=status,
            anonymous=(i % 5 == 0),
            assigned_department=DEPT_MAP.get(cat, "General Administration"),
            ai_recommendation=f"Investigate and resolve the {cat} issue as soon as possible.",
            resolved_at=resolved_at
        )
        c.created_at = created
        db.add(c)
        db.flush()
        complaint_objects.append(c)

    # Community Support ("I am also affected")
    for c in complaint_objects:
        supporters = random.sample(user_objects, min(random.randint(0, 4), len(user_objects)))
        for sup_user in supporters:
            if sup_user.id != c.user_id:
                support = ComplaintSupport(
                    organization_id=org.id, complaint_id=c.id, user_id=sup_user.id
                )
                db.add(support)
                db.flush()
                # Recompute impact score
                support_count = len(supporters)
                c.impact_score = round((c.severity_score * 0.6) + (support_count * 0.4), 2)

    # Feedback
    feedback_msgs = [
        ("Overall", 4, "The platform is very helpful for submitting concerns quickly."),
        ("Mess", 2, "Mess quality has gone down significantly this semester."),
        ("WiFi", 3, "Internet is okay but needs improvement in hostel areas."),
        ("Hostel", 4, "Room maintenance has improved over the last month."),
        ("Transport", 3, "Bus timings could be more punctual."),
        ("Academic", 5, "Faculty is very responsive and helpful this semester."),
        ("Overall", 3, "Platform is good but the app needs more features."),
    ]
    for i, (cat, rating, msg) in enumerate(feedback_msgs):
        u = user_objects[i % len(user_objects)]
        fb = Feedback(
            organization_id=org.id, user_id=u.id,
            category=cat, rating=rating, message=msg
        )
        db.add(fb)

    # Notifications
    for u in user_objects[:3]:
        notif = Notification(
            organization_id=org.id, user_id=u.id,
            message="Welcome to EchoCampus AI! Submit your first complaint or feedback.",
            is_read=False
        )
        db.add(notif)

    db.commit()
    print(f"[OK] Created org: {org_name} | Workspace: {workspace_code} | Invite: {invite_code}")
    print(f"     Admin: {admin_email} / Admin@123")
    print(f"     Students login with Student@123 | workspace: {workspace_code}")
    return org


def main():
    # Clean existing data for fresh seed
    print("Clearing existing data...")
    db.query(ComplaintSupport).delete()
    db.query(Notification).delete()
    db.query(Feedback).delete()
    db.query(Complaint).delete()
    db.query(User).delete()
    db.query(Organization).delete()
    db.commit()

    # ─── Org 1: Medicaps University ────────────────────────────────────────
    create_org_data(
        org_name="Medicaps University",
        org_type="University",
        workspace_code="medicaps",
        invite_code="MCPX92",
        admin_name="Dr. Rajesh Sharma",
        admin_email="admin@medicaps.edu",
        students=[
            ("Aarav Patel", "aarav@medicaps.edu"),
            ("Priya Verma", "priya@medicaps.edu"),
            ("Rohan Gupta", "rohan@medicaps.edu"),
            ("Sneha Singh", "sneha@medicaps.edu"),
            ("Arjun Kumar", "arjun@medicaps.edu"),
        ]
    )

    # ─── Org 2: IIT Indore ─────────────────────────────────────────────────
    create_org_data(
        org_name="IIT Indore",
        org_type="University",
        workspace_code="iitindore",
        invite_code="IITI77",
        admin_name="Prof. Suresh Nair",
        admin_email="admin@iitindore.ac.in",
        students=[
            ("Vikram Rao", "vikram@iitindore.ac.in"),
            ("Ananya Joshi", "ananya@iitindore.ac.in"),
            ("Dev Malhotra", "dev@iitindore.ac.in"),
            ("Meera Iyer", "meera@iitindore.ac.in"),
        ]
    )

    print("\n" + "="*60)
    print("  EchoCampus AI V2.0 – Seed Complete!")
    print("="*60)
    print("\n  Workspace 1: medicaps  |  Invite: MCPX92")
    print("  Workspace 2: iitindore |  Invite: IITI77")
    print("\n  Admin Password : Admin@123")
    print("  Student Password: Student@123")
    print("="*60)


if __name__ == "__main__":
    main()
