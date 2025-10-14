import json
import hashlib
from typing import Optional, List, Dict
import redis
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.core.config import settings


class SemanticCache:
    """Semantic caching using embeddings for similar query detection."""

    def __init__(self):
        self.enabled = settings.ENABLE_SEMANTIC_CACHE
        if self.enabled:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self.similarity_threshold = settings.CACHE_SIMILARITY_THRESHOLD
            self.ttl = settings.CACHE_TTL

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        return self.embedding_model.encode([text])[0]

    def _get_cache_key(self, query: str, context: str = "") -> str:
        """Generate cache key from query and context."""
        combined = f"{query}:{context}"
        return hashlib.md5(combined.encode()).hexdigest()

    async def get(self, query: str, context: str = "", messages: List[Dict] = None) -> Optional[str]:
        """
        Retrieve cached response if semantically similar query exists.

        Args:
            query: User's query
            context: Additional context (e.g., interview type, role)
            messages: Recent conversation messages for context
        """
        if not self.enabled:
            return None

        try:
            # Generate embedding for current query
            query_embedding = self._generate_embedding(query)

            # Search for similar cached queries
            pattern = f"cache:query:*"
            cached_keys = self.redis_client.keys(pattern)

            best_similarity = 0.0
            best_match_key = None

            for key in cached_keys[:100]:  # Limit search to recent 100 entries
                try:
                    cached_data = self.redis_client.get(key)
                    if not cached_data:
                        continue

                    cached_obj = json.loads(cached_data)
                    cached_embedding = np.array(cached_obj.get("embedding", []))

                    if cached_embedding.size == 0:
                        continue

                    # Calculate cosine similarity
                    similarity = cosine_similarity(
                        query_embedding.reshape(1, -1),
                        cached_embedding.reshape(1, -1)
                    )[0][0]

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match_key = key

                except Exception as e:
                    continue

            # Return cached response if similarity exceeds threshold
            if best_similarity >= self.similarity_threshold and best_match_key:
                cached_data = json.loads(self.redis_client.get(best_match_key))
                print(f"[CACHE HIT] Similarity: {best_similarity:.4f}")
                return cached_data.get("response")

            print(f"[CACHE MISS] Best similarity: {best_similarity:.4f}")
            return None

        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None

    async def set(self, query: str, response: str, context: str = ""):
        """
        Cache query-response pair with embedding.

        Args:
            query: User's query
            response: AI response
            context: Additional context
        """
        if not self.enabled:
            return

        try:
            # Generate embedding
            embedding = self._generate_embedding(query)

            # Create cache entry
            cache_entry = {
                "query": query,
                "response": response,
                "context": context,
                "embedding": embedding.tolist()
            }

            # Store in Redis with TTL
            cache_key = f"cache:query:{self._get_cache_key(query, context)}"
            self.redis_client.setex(
                cache_key,
                self.ttl,
                json.dumps(cache_entry)
            )
            print(f"[CACHE SET] Stored response for query")

        except Exception as e:
            print(f"Cache storage error: {e}")

    async def clear(self):
        """Clear all cached entries."""
        if not self.enabled:
            return

        try:
            pattern = "cache:query:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                print(f"[CACHE CLEAR] Removed {len(keys)} entries")
        except Exception as e:
            print(f"Cache clear error: {e}")


# Global cache instance
semantic_cache = SemanticCache()
