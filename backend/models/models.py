from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from backend.database.connection import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'University', 'College', 'School', 'Hostel', 'Student Club', 'Coaching Institute'
    workspace_code = Column(String, unique=True, index=True, nullable=False)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    logo_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="organization")
    complaints = relationship("Complaint", back_populates="organization")
    feedbacks = relationship("Feedback", back_populates="organization")
    notifications = relationship("Notification", back_populates="organization")
    supports = relationship("ComplaintSupport", back_populates="organization")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'student', 'moderator', 'admin', 'super_admin'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="users")
    complaints = relationship("Complaint", back_populates="user", foreign_keys="[Complaint.user_id]")
    feedbacks = relationship("Feedback", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    supports = relationship("ComplaintSupport", back_populates="user")

    __table_args__ = (UniqueConstraint('organization_id', 'email', name='_org_email_uc'),)

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # 'Hostel', 'Mess', 'WiFi', 'Transport', 'Academic', 'Infrastructure', 'Security', 'Other'
    sentiment = Column(String, nullable=False)  # 'Positive', 'Neutral', 'Negative'
    priority = Column(String, nullable=False)  # 'Low', 'Medium', 'High', 'Critical'
    severity_score = Column(Integer, default=50)  # 0 to 100
    impact_score = Column(Float, default=50.0)
    status = Column(String, default="Pending")  # 'Pending', 'In Progress', 'Resolved', 'Rejected', 'Escalated'
    image_path = Column(String, nullable=True)
    anonymous = Column(Boolean, default=False)
    assigned_department = Column(String, nullable=False)
    assigned_to = Column(String, nullable=True)
    duplicate_score = Column(Float, nullable=True)
    parent_complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    ai_recommendation = Column(Text, nullable=True)
    resolution_rating = Column(Integer, nullable=True)
    resolution_comment = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="complaints")
    user = relationship("User", back_populates="complaints", foreign_keys=[user_id])
    supports = relationship("ComplaintSupport", back_populates="complaint", cascade="all, delete-orphan")
    duplicates = relationship("Complaint", backref=backref("parent", remote_side=[id]))

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, default="Overall")
    rating = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="notifications")
    user = relationship("User", back_populates="notifications")

class ComplaintSupport(Base):
    __tablename__ = "complaint_supports"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="supports")
    complaint = relationship("Complaint", back_populates="supports")
    user = relationship("User", back_populates="supports")

    __table_args__ = (UniqueConstraint('complaint_id', 'user_id', name='_complaint_user_support_uc'),)
