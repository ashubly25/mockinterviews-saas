import tiktoken
from typing import List, Dict
from app.core.config import settings


class PromptCompressor:
    """Compress prompts to reduce token usage while preserving key information."""

    def __init__(self):
        self.enabled = settings.ENABLE_PROMPT_COMPRESSION
        self.max_tokens = settings.MAX_CONTEXT_TOKENS
        self.compression_ratio = settings.COMPRESSION_RATIO
        self.min_length = settings.MIN_MESSAGE_LENGTH
        self.encoder = tiktoken.encoding_for_model("gpt-4")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoder.encode(text))

    def compress_message(self, content: str) -> str:
        """
        Compress a single message by extracting key sentences.

        Strategy:
        - Keep first and last sentences (context boundaries)
        - Extract sentences with keywords (questions, technical terms)
        - Remove filler words and redundant phrases
        """
        if not self.enabled or len(content) < self.min_length:
            return content

        sentences = content.split('. ')
        if len(sentences) <= 2:
            return content

        # Calculate target sentence count
        target_count = max(2, int(len(sentences) * self.compression_ratio))

        # Always keep first and last sentence
        compressed = [sentences[0]]

        # Score middle sentences by importance
        middle_sentences = sentences[1:-1]
        scored_sentences = []

        keywords = [
            'what', 'how', 'why', 'when', 'where', 'which',
            'explain', 'describe', 'implement', 'design', 'optimize',
            'algorithm', 'complexity', 'pattern', 'solution', 'approach',
            'interview', 'question', 'answer', 'example'
        ]

        for sent in middle_sentences:
            score = sum(1 for keyword in keywords if keyword in sent.lower())
            scored_sentences.append((score, sent))

        # Sort by score and keep top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [sent for _, sent in scored_sentences[:target_count-2]]

        compressed.extend(top_sentences)
        compressed.append(sentences[-1])

        return '. '.join(compressed) + '.'

    def compress_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Compress a list of messages to fit within token limit.

        Strategy:
        - Keep recent messages intact (KEEP_RECENT_MESSAGES)
        - Compress older messages
        - Remove very old messages if still over limit
        """
        if not self.enabled:
            return messages

        total_tokens = sum(self.count_tokens(msg['content']) for msg in messages)

        if total_tokens <= self.max_tokens:
            return messages

        print(f"[COMPRESSION] Total tokens: {total_tokens}, compressing...")

        # Keep recent messages uncompressed
        keep_recent = settings.KEEP_RECENT_MESSAGES
        recent_messages = messages[-keep_recent:]
        older_messages = messages[:-keep_recent]

        # Compress older messages
        compressed_older = []
        for msg in older_messages:
            compressed_content = self.compress_message(msg['content'])
            compressed_older.append({
                'role': msg['role'],
                'content': compressed_content
            })

        # Combine and check tokens again
        all_messages = compressed_older + recent_messages
        total_tokens = sum(self.count_tokens(msg['content']) for msg in all_messages)

        # If still over limit, progressively remove oldest messages
        while total_tokens > self.max_tokens and len(compressed_older) > 2:
            compressed_older.pop(0)
            all_messages = compressed_older + recent_messages
            total_tokens = sum(self.count_tokens(msg['content']) for msg in all_messages)

        final_tokens = sum(self.count_tokens(msg['content']) for msg in all_messages)
        print(f"[COMPRESSION] Compressed to {final_tokens} tokens ({len(all_messages)} messages)")

        return all_messages

    def estimate_tokens(self, messages: List[Dict[str, str]], system_prompt: str = "") -> int:
        """Estimate total tokens for messages and system prompt."""
        total = self.count_tokens(system_prompt)
        total += sum(self.count_tokens(msg['content']) for msg in messages)
        return total


# Global compressor instance
prompt_compressor = PromptCompressor()
