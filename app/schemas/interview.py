from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class InterviewSessionCreate(BaseModel):
    """Schema for creating an interview session."""

    interview_type: Literal["technical", "behavioral", "system_design", "case_study"]
    role: str = Field(..., description="Job role, e.g., 'Software Engineer'")
    level: Literal["junior", "mid", "senior", "staff", "principal"]
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: str
    session_id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class InterviewSessionResponse(BaseModel):
    """Schema for interview session response."""

    id: str
    interview_type: str
    role: str
    level: str
    focus_areas: Optional[List[str]]
    status: str
    created_at: datetime
    ended_at: Optional[datetime]
    overall_score: Optional[float]
    feedback: Optional[str]

    class Config:
        from_attributes = True


class InterviewSessionDetail(InterviewSessionResponse):
    """Detailed session response including messages."""

    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Schema for conversation exchange."""

    user_message: MessageResponse
    assistant_message: MessageResponse


class FeedbackResponse(BaseModel):
    """Schema for interview feedback."""

    session_id: str
    overall_score: float
    feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]
    detailed_analysis: dict
