from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.interview import (
    InterviewSessionCreate,
    InterviewSessionResponse,
    InterviewSessionDetail,
    MessageCreate,
    ConversationResponse,
    FeedbackResponse,
    MessageResponse
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])
interview_service = InterviewService()


@router.post("/sessions", response_model=InterviewSessionDetail, status_code=201)
async def create_session(
    session_data: InterviewSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new interview session.

    This endpoint initializes a new interview and returns the first question from the AI interviewer.
    """
    try:
        session = await interview_service.create_session(db, session_data)
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[InterviewSessionResponse])
async def get_sessions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all interview sessions."""
    sessions = interview_service.get_sessions(db, skip, limit)
    return sessions


@router.get("/sessions/{session_id}", response_model=InterviewSessionDetail)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific interview session with full conversation history."""
    session = interview_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/messages", response_model=ConversationResponse)
async def send_message(
    session_id: str,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    Send a message in an interview session.

    The AI interviewer will respond to your message with the next question or feedback.
    All optimizations (caching, compression, model routing) are applied automatically.
    """
    try:
        result = await interview_service.send_message(db, session_id, message_data)
        return {
            "user_message": result["user_message"],
            "assistant_message": result["assistant_message"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/end", response_model=FeedbackResponse)
async def end_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    End an interview session and receive comprehensive feedback.

    This generates an AI-powered evaluation with scores, strengths, and areas for improvement.
    """
    try:
        feedback = await interview_service.end_session(db, session_id)
        feedback["session_id"] = session_id
        return feedback
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get all messages for a specific session."""
    session = interview_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.messages
