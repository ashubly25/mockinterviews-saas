from typing import List, Dict, Literal
from enum import Enum
import tiktoken
from app.core.config import settings


class ComplexityLevel(Enum):
    """Enum for query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ModelRouter:
    """
    Route queries to appropriate models based on complexity.

    Strategy:
    - SIMPLE: Short queries, greetings, acknowledgments -> Small model (Haiku, GPT-3.5)
    - MODERATE: Standard interview questions -> Small model
    - COMPLEX: Technical deep-dives, system design, code review -> Large model (Sonnet, GPT-4)
    """

    def __init__(self):
        self.enabled = settings.ENABLE_MODEL_ROUTING
        self.threshold = settings.ROUTING_COMPLEXITY_THRESHOLD
        self.encoder = tiktoken.encoding_for_model("gpt-4")

    def analyze_complexity(self, query: str, conversation_history: List[Dict] = None) -> ComplexityLevel:
        """
        Analyze query complexity to determine which model to use.

        Factors:
        1. Token count
        2. Presence of technical keywords
        3. Code blocks
        4. Question depth
        """
        token_count = len(self.encoder.encode(query))

        # Technical complexity indicators
        technical_keywords = [
            'algorithm', 'complexity', 'optimize', 'design', 'architecture',
            'implement', 'debug', 'refactor', 'scale', 'performance',
            'system design', 'data structure', 'big o', 'concurrency',
            'distributed', 'microservices', 'database', 'optimization'
        ]

        code_indicators = ['```', 'def ', 'class ', 'function', 'const ', 'let ', 'var ']

        # Check for code blocks
        has_code = any(indicator in query.lower() for indicator in code_indicators)

        # Check for technical terms
        technical_term_count = sum(
            1 for keyword in technical_keywords
            if keyword in query.lower()
        )

        # Simple queries (use small model)
        if token_count < 20 and technical_term_count == 0 and not has_code:
            return ComplexityLevel.SIMPLE

        # Complex queries (use large model)
        if any([
            token_count > self.threshold,
            technical_term_count >= 3,
            has_code,
            'explain in detail' in query.lower(),
            'step by step' in query.lower(),
            'system design' in query.lower()
        ]):
            return ComplexityLevel.COMPLEX

        # Default to moderate
        return ComplexityLevel.MODERATE

    def select_model(
        self,
        query: str,
        conversation_history: List[Dict] = None,
        provider: str = None
    ) -> Dict[str, str]:
        """
        Select appropriate model based on query complexity.

        Returns:
            Dict with 'model' and 'reasoning'
        """
        if not self.enabled:
            # Use default large model if routing disabled
            provider = provider or settings.AI_PROVIDER
            model = (
                settings.ANTHROPIC_LARGE_MODEL
                if provider == "anthropic"
                else settings.OPENAI_LARGE_MODEL
            )
            return {"model": model, "reasoning": "routing_disabled"}

        complexity = self.analyze_complexity(query, conversation_history)
        provider = provider or settings.AI_PROVIDER

        # Route to appropriate model
        if complexity == ComplexityLevel.SIMPLE or complexity == ComplexityLevel.MODERATE:
            model = (
                settings.ANTHROPIC_SMALL_MODEL
                if provider == "anthropic"
                else settings.OPENAI_SMALL_MODEL
            )
            reasoning = f"small_model_{complexity.value}"
        else:
            model = (
                settings.ANTHROPIC_LARGE_MODEL
                if provider == "anthropic"
                else settings.OPENAI_LARGE_MODEL
            )
            reasoning = f"large_model_{complexity.value}"

        print(f"[MODEL ROUTING] Complexity: {complexity.value} -> Model: {model}")

        return {
            "model": model,
            "reasoning": reasoning,
            "complexity": complexity.value,
            "token_count": len(self.encoder.encode(query))
        }

    def get_fallback_model(self, failed_model: str, provider: str) -> str:
        """
        Get fallback model if primary model fails.

        Fallback strategy:
        1. Try smaller model from same provider
        2. Try alternative provider
        """
        if not settings.ENABLE_FALLBACK:
            raise Exception("No fallback available")

        print(f"[FALLBACK] Primary model {failed_model} failed, using fallback...")

        if provider == "anthropic":
            # Try Haiku if Sonnet failed
            if failed_model == settings.ANTHROPIC_LARGE_MODEL:
                return settings.ANTHROPIC_SMALL_MODEL
            # Try OpenAI as last resort
            return settings.OPENAI_SMALL_MODEL
        else:
            # Try GPT-3.5 if GPT-4 failed
            if failed_model == settings.OPENAI_LARGE_MODEL:
                return settings.OPENAI_SMALL_MODEL
            # Try Claude as last resort
            return settings.ANTHROPIC_SMALL_MODEL


# Global router instance
model_router = ModelRouter()
