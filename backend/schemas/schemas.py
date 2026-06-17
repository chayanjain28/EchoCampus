from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ─── Organization ──────────────────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    """Payload for Admin creating a new workspace."""
    # Admin info
    admin_name: str = Field(..., min_length=2, max_length=60)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6)
    # Organization info
    organization_name: str = Field(..., min_length=2, max_length=100)
    organization_type: str  # 'University', 'College', 'School', 'Hostel', 'Student Club', 'Coaching Institute'
    workspace_code: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-z0-9_-]+$")
    description: Optional[str] = None
    logo_url: Optional[str] = None

class OrganizationJoin(BaseModel):
    """Payload for Student/Moderator joining an existing workspace via invite code."""
    name: str = Field(..., min_length=2, max_length=60)
    email: EmailStr
    password: str = Field(..., min_length=6)
    workspace_code: str
    invite_code: str

class UserLogin(BaseModel):
    workspace_code: str
    email: EmailStr
    password: str

class OrganizationResponse(BaseModel):
    id: int
    name: str
    type: str
    workspace_code: str
    invite_code: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class OrganizationUpdate(BaseModel):
    """Admin can update organization settings."""
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None

# ─── User ──────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: OrganizationResponse

# ─── Complaint ─────────────────────────────────────────────────────────────

class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    anonymous: bool = False
    image_path: Optional[str] = None

class ComplaintDetailResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    title: str
    description: str
    category: str
    sentiment: str
    priority: str
    severity_score: int
    impact_score: float
    status: str
    image_path: Optional[str] = None
    anonymous: bool
    assigned_department: str
    assigned_to: Optional[str] = None
    duplicate_score: Optional[float] = None
    parent_complaint_id: Optional[int] = None
    ai_recommendation: Optional[str] = None
    resolution_rating: Optional[int] = None
    resolution_comment: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    student_name: str
    duplicate_count: int = 0
    support_count: int = 0
    user_has_supported: bool = False

    class Config:
        from_attributes = True

class ComplaintStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(Pending|In Progress|Resolved|Rejected|Escalated)$")
    assigned_to: Optional[str] = None
    assigned_department: Optional[str] = None

class ResolutionRate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

# ─── Feedback ──────────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    category: str = "Overall"
    rating: int = Field(..., ge=1, le=5)
    message: str = Field(..., min_length=5)

class FeedbackResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    category: str
    rating: int
    message: str
    created_at: datetime
    student_name: str

    class Config:
        from_attributes = True

# ─── Notification ──────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ─── Analytics ─────────────────────────────────────────────────────────────

class CSSIResponse(BaseModel):
    category: str
    score: float

class AnalyticsDashboard(BaseModel):
    campus_health_score: int
    student_satisfaction_index: float
    admin_efficiency_score: int
    avg_resolution_time: float
    most_reported_service: str
    most_supported_issue: Optional[str] = None
    total_affected_students: int
    escalated_complaints_count: int
    duplicate_groups_count: int
    total_active_issues: int
    total_complaints: int
    total_students: int
    cssi: List[CSSIResponse]
