from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base
import uuid

def generate_key():
    return str(uuid.uuid4())[:8].upper()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # teacher / student
    is_verified = Column(Boolean, default=False)
    verify_code = Column(String(10), nullable=True)
    reset_code = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    groups_owned = relationship("Group", back_populates="teacher")
    memberships = relationship("GroupMember", back_populates="student")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invite_key = Column(String(20), unique=True, default=generate_key, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User", back_populates="groups_owned")
    members = relationship("GroupMember", back_populates="group")
    assignments = relationship("Assignment", back_populates="group")

class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="members")
    student = relationship("User", back_populates="memberships")

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    is_timer = Column(Boolean, default=False)
    timer_minutes = Column(Integer, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    ai_score = Column(Float, nullable=True)
    ai_comment = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    is_late = Column(Boolean, default=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User")
