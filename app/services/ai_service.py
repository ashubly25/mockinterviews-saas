from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import anthropic
import openai
from app.core.config import settings
from app.services.model_router import model_router
from app.services.cache_service import semantic_cache
from app.services.compression_service import prompt_compressor
from app.services.summarization_service import session_summarizer


class AIService(ABC):
    """Abstract base class for AI services with optimization features."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        model: Optional[str] = None
    ) -> str:
        """Generate a response from the AI model."""
        pass


class AnthropicService(AIService):
    """Service for interacting with Anthropic's Claude API."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.provider = "anthropic"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        model: Optional[str] = None
    ) -> str:
        """Generate a response using Claude with optimizations."""
        # Use provided model or route based on complexity
        if not model:
            last_message = messages[-1]['content'] if messages else ""
            routing_result = model_router.select_model(
                query=last_message,
                conversation_history=messages,
                provider=self.provider
            )
            model = routing_result['model']
            print(f"[AI SERVICE] Using model: {model} (reason: {routing_result['reasoning']})")

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text

        except Exception as e:
            # Fallback on error
            if settings.ENABLE_FALLBACK:
                fallback_model = model_router.get_fallback_model(model, self.provider)
                print(f"[FALLBACK] Retrying with {fallback_model}")
                response = self.client.messages.create(
                    model=fallback_model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=messages
                )
                return response.content[0].text
            raise Exception(f"Error generating response from Claude: {str(e)}")


class OpenAIService(AIService):
    """Service for interacting with OpenAI's API."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.provider = "openai"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        model: Optional[str] = None
    ) -> str:
        """Generate a response using OpenAI with optimizations."""
        # Use provided model or route based on complexity
        if not model:
            last_message = messages[-1]['content'] if messages else ""
            routing_result = model_router.select_model(
                query=last_message,
                conversation_history=messages,
                provider=self.provider
            )
            model = routing_result['model']
            print(f"[AI SERVICE] Using model: {model} (reason: {routing_result['reasoning']})")

        try:
            # Prepend system message to messages
            full_messages = [{"role": "system", "content": system_prompt}] + messages

            response = self.client.chat.completions.create(
                model=model,
                messages=full_messages,
                max_tokens=2000
            )
            return response.choices[0].message.content

        except Exception as e:
            # Fallback on error
            if settings.ENABLE_FALLBACK:
                fallback_model = model_router.get_fallback_model(model, self.provider)
                print(f"[FALLBACK] Retrying with {fallback_model}")
                full_messages = [{"role": "system", "content": system_prompt}] + messages
                response = self.client.chat.completions.create(
                    model=fallback_model,
                    messages=full_messages,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            raise Exception(f"Error generating response from OpenAI: {str(e)}")


class OptimizedAIService:
    """
    Wrapper service that applies all optimizations:
    - Semantic caching
    - Model routing
    - Prompt compression
    - Session summarization
    """

    def __init__(self, base_service: AIService):
        self.base_service = base_service

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        session_id: str = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate optimized response with all optimization layers.

        Returns:
            Dict with 'response', 'cached', 'model_used', 'token_usage'
        """
        last_message = messages[-1]['content'] if messages else ""

        # 1. Check semantic cache
        if use_cache:
            cached_response = await semantic_cache.get(
                query=last_message,
                context=system_prompt[:100],
                messages=messages
            )
            if cached_response:
                return {
                    "response": cached_response,
                    "cached": True,
                    "model_used": "cache",
                    "optimizations_applied": ["semantic_cache"]
                }

        optimizations_applied = []

        # 2. Apply session summarization if needed
        if await session_summarizer.should_summarize(len(messages)):
            summary_result = await session_summarizer.summarize_session(
                messages, self.base_service
            )
            messages = summary_result['messages']
            if summary_result['summary']:
                optimizations_applied.append("session_summarization")

        # 3. Apply prompt compression
        original_token_count = prompt_compressor.estimate_tokens(messages, system_prompt)
        compressed_messages = prompt_compressor.compress_messages(messages)
        compressed_token_count = prompt_compressor.estimate_tokens(compressed_messages, system_prompt)

        if compressed_token_count < original_token_count:
            messages = compressed_messages
            optimizations_applied.append("prompt_compression")

        # 4. Generate response (with automatic model routing)
        response = await self.base_service.generate_response(
            messages=messages,
            system_prompt=system_prompt
        )
        optimizations_applied.append("model_routing")

        # 5. Cache the response
        if use_cache:
            await semantic_cache.set(
                query=last_message,
                response=response,
                context=system_prompt[:100]
            )

        return {
            "response": response,
            "cached": False,
            "optimizations_applied": optimizations_applied,
            "token_usage": {
                "original": original_token_count,
                "compressed": compressed_token_count,
                "saved": original_token_count - compressed_token_count
            }
        }


def get_ai_service() -> OptimizedAIService:
    """Factory function to get the optimized AI service."""
    if settings.AI_PROVIDER == "anthropic":
        base_service = AnthropicService()
    elif settings.AI_PROVIDER == "openai":
        base_service = OpenAIService()
    else:
        raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")

    return OptimizedAIService(base_service)
