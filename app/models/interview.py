from sqlalchemy import Column, String, DateTime, JSON, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class InterviewSession(Base):
    """Interview session model."""

    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_type = Column(String, nullable=False)  # technical, behavioral, system_design
    role = Column(String, nullable=False)
    level = Column(String, nullable=False)  # junior, mid, senior, staff
    focus_areas = Column(JSON, nullable=True)
    status = Column(String, default="active")  # active, completed, abandoned
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    overall_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InterviewSession {self.id} - {self.interview_type}>"


class Message(Base):
    """Message model for interview conversation."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("interview_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)

    # Relationships
    session = relationship("InterviewSession", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.id} - {self.role}>"
