from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.interview import InterviewSession, Message
from app.schemas.interview import InterviewSessionCreate, MessageCreate
from app.services.ai_service import get_ai_service


class InterviewService:
    """Business logic for managing interview sessions."""

    def __init__(self):
        self.ai_service = get_ai_service()

    def get_system_prompt(self, session: InterviewSession) -> str:
        """Generate system prompt based on interview configuration."""
        prompts = {
            "technical": f"""You are an expert technical interviewer conducting a {session.level} level interview for a {session.role} position.

Your responsibilities:
- Ask relevant technical questions about algorithms, data structures, and problem-solving
- Evaluate code quality, efficiency, and design choices
- Provide constructive feedback and hints when needed
- Assess problem-solving approach and communication skills
- Be professional, encouraging, and respectful

Focus areas: {', '.join(session.focus_areas) if session.focus_areas else 'general technical skills'}

Conduct a realistic interview experience. Start with an appropriate opening question.""",

            "behavioral": f"""You are an experienced HR interviewer conducting a {session.level} level behavioral interview for a {session.role} position.

Your responsibilities:
- Ask behavioral questions using the STAR method (Situation, Task, Action, Result)
- Evaluate leadership, teamwork, conflict resolution, and communication
- Probe deeper into responses to understand true experiences
- Assess cultural fit and soft skills
- Be empathetic and create a comfortable environment

Focus areas: {', '.join(session.focus_areas) if session.focus_areas else 'general behavioral assessment'}

Conduct a realistic behavioral interview. Start with an appropriate opening question.""",

            "system_design": f"""You are a senior architect conducting a {session.level} level system design interview for a {session.role} position.

Your responsibilities:
- Present realistic system design problems (e.g., design Twitter, URL shortener, etc.)
- Guide through requirements gathering, capacity estimation, and architecture
- Evaluate scalability, reliability, and trade-off analysis
- Discuss database choices, caching strategies, load balancing
- Assess breadth of knowledge and practical experience

Focus areas: {', '.join(session.focus_areas) if session.focus_areas else 'general system design'}

Conduct a realistic system design interview. Start with presenting a system design problem.""",

            "case_study": f"""You are a management consultant conducting a {session.level} level case study interview for a {session.role} position.

Your responsibilities:
- Present business case problems requiring analytical thinking
- Evaluate structured problem-solving and business acumen
- Assess quantitative reasoning and estimation skills
- Probe assumptions and logical reasoning
- Provide clarifications when asked

Focus areas: {', '.join(session.focus_areas) if session.focus_areas else 'general case study'}

Conduct a realistic case study interview. Start with presenting the case."""
        }

        return prompts.get(session.interview_type, prompts["technical"])

    async def create_session(self, db: Session, session_data: InterviewSessionCreate) -> InterviewSession:
        """Create a new interview session."""
        session = InterviewSession(
            interview_type=session_data.interview_type,
            role=session_data.role,
            level=session_data.level,
            focus_areas=session_data.focus_areas,
            status="active"
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Generate initial interviewer message
        system_prompt = self.get_system_prompt(session)
        initial_messages = [
            {"role": "user", "content": f"Hello, I'm ready for the {session_data.interview_type} interview."}
        ]

        response_data = await self.ai_service.generate_response(
            messages=initial_messages,
            system_prompt=system_prompt,
            session_id=session.id
        )

        # Save initial exchange
        user_msg = Message(
            session_id=session.id,
            role="user",
            content=initial_messages[0]["content"]
        )
        ai_msg = Message(
            session_id=session.id,
            role="assistant",
            content=response_data['response'],
            metadata={"optimizations": response_data.get('optimizations_applied', [])}
        )

        db.add(user_msg)
        db.add(ai_msg)
        db.commit()

        return session

    async def send_message(
        self,
        db: Session,
        session_id: str,
        message_data: MessageCreate
    ) -> Dict:
        """Send a message in an interview session."""
        # Get session
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()

        if not session:
            raise ValueError("Session not found")

        if session.status != "active":
            raise ValueError("Session is not active")

        # Save user message
        user_msg = Message(
            session_id=session_id,
            role="user",
            content=message_data.content
        )
        db.add(user_msg)
        db.commit()

        # Get conversation history
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.timestamp).all()

        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Generate AI response with optimizations
        system_prompt = self.get_system_prompt(session)
        response_data = await self.ai_service.generate_response(
            messages=conversation_history,
            system_prompt=system_prompt,
            session_id=session_id
        )

        # Save AI response
        ai_msg = Message(
            session_id=session_id,
            role="assistant",
            content=response_data['response'],
            metadata={
                "cached": response_data.get('cached', False),
                "optimizations": response_data.get('optimizations_applied', []),
                "token_usage": response_data.get('token_usage', {})
            }
        )
        db.add(ai_msg)
        db.commit()
        db.refresh(ai_msg)

        return {
            "user_message": user_msg,
            "assistant_message": ai_msg,
            "metadata": ai_msg.metadata
        }

    async def end_session(self, db: Session, session_id: str) -> Dict:
        """End an interview session and generate feedback."""
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()

        if not session:
            raise ValueError("Session not found")

        # Get all messages
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.timestamp).all()

        # Generate feedback
        feedback = await self._generate_feedback(session, messages)

        # Update session
        session.status = "completed"
        session.ended_at = datetime.utcnow()
        session.overall_score = feedback['overall_score']
        session.feedback = feedback['feedback']

        db.commit()
        db.refresh(session)

        return feedback

    async def _generate_feedback(
        self,
        session: InterviewSession,
        messages: List[Message]
    ) -> Dict:
        """Generate comprehensive feedback for the interview."""
        conversation = "\n\n".join([
            f"{msg.role.upper()}: {msg.content}"
            for msg in messages
        ])

        feedback_prompt = f"""As an expert interviewer, provide comprehensive feedback for this {session.interview_type} interview for a {session.level} {session.role} position.

CONVERSATION:
{conversation}

Provide feedback in the following JSON format:
{{
    "overall_score": <float 0-10>,
    "feedback": "<detailed paragraph>",
    "strengths": ["strength1", "strength2", ...],
    "areas_for_improvement": ["area1", "area2", ...],
    "detailed_analysis": {{
        "technical_skills": "<assessment>",
        "communication": "<assessment>",
        "problem_solving": "<assessment>",
        "specific_observations": "<detailed notes>"
    }}
}}
"""

        system_prompt = "You are an expert interview evaluator. Provide honest, constructive, and actionable feedback."

        response = await self.ai_service.base_service.generate_response(
            messages=[{"role": "user", "content": feedback_prompt}],
            system_prompt=system_prompt
        )

        # Parse JSON response
        import json
        try:
            feedback_data = json.loads(response)
            return feedback_data
        except:
            # Fallback if JSON parsing fails
            return {
                "overall_score": 7.0,
                "feedback": response,
                "strengths": [],
                "areas_for_improvement": [],
                "detailed_analysis": {}
            }

    def get_session(self, db: Session, session_id: str) -> InterviewSession:
        """Get interview session by ID."""
        return db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()

    def get_sessions(self, db: Session, skip: int = 0, limit: int = 10) -> List[InterviewSession]:
        """Get all interview sessions."""
        return db.query(InterviewSession).order_by(
            InterviewSession.created_at.desc()
        ).offset(skip).limit(limit).all()
