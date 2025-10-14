from typing import List, Dict
from app.core.config import settings


class SessionSummarizer:
    """Summarize conversation sessions to maintain context with reduced tokens."""

    def __init__(self):
        self.enabled = settings.ENABLE_SESSION_SUMMARIZATION
        self.trigger_count = settings.SUMMARIZATION_TRIGGER
        self.keep_recent = settings.KEEP_RECENT_MESSAGES

    async def should_summarize(self, message_count: int) -> bool:
        """Check if session should be summarized."""
        return self.enabled and message_count >= self.trigger_count

    def create_summary_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Create prompt for AI to summarize conversation."""
        conversation = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages
        ])

        return f"""Summarize the following interview conversation, preserving:
1. Key questions asked by the interviewer
2. Main points discussed by the candidate
3. Technical concepts and solutions mentioned
4. Any code or algorithms discussed
5. Feedback or evaluations provided

Keep the summary concise but comprehensive (max 300 words).

CONVERSATION:
{conversation}

SUMMARY:"""

    async def summarize_session(
        self,
        messages: List[Dict[str, str]],
        ai_service
    ) -> Dict[str, str]:
        """
        Summarize older messages and return compressed format.

        Returns:
            Dict with 'summary' message and 'recent' messages
        """
        if not self.enabled or len(messages) < self.trigger_count:
            return {"messages": messages, "summary": None}

        # Split into older and recent messages
        messages_to_summarize = messages[:-self.keep_recent]
        recent_messages = messages[-self.keep_recent:]

        if not messages_to_summarize:
            return {"messages": messages, "summary": None}

        # Generate summary using AI
        summary_prompt = self.create_summary_prompt(messages_to_summarize)

        try:
            summary = await ai_service.generate_response(
                messages=[{"role": "user", "content": summary_prompt}],
                system_prompt="You are a conversation summarizer. Create concise, informative summaries."
            )

            print(f"[SUMMARIZATION] Compressed {len(messages_to_summarize)} messages into summary")

            # Return summary as system message + recent messages
            summary_message = {
                "role": "assistant",
                "content": f"[CONVERSATION SUMMARY]\n{summary}\n[END SUMMARY]\n\nContinuing conversation..."
            }

            return {
                "messages": [summary_message] + recent_messages,
                "summary": summary
            }

        except Exception as e:
            print(f"[SUMMARIZATION ERROR] {e}")
            return {"messages": messages, "summary": None}

    def format_with_summary(self, summary: str, recent_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages with summary prefix."""
        summary_msg = {
            "role": "assistant",
            "content": f"[Previous conversation summary: {summary}]"
        }
        return [summary_msg] + recent_messages


# Global summarizer instance
session_summarizer = SessionSummarizer()
