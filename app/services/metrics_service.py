from typing import Dict, Any
from app.api.metrics import (
    cache_hits,
    cache_misses,
    model_usage,
    token_usage,
    optimization_applied,
    request_count,
    response_time
)
from app.core.config import settings
import time


class MetricsCollector:
    """Collect and track metrics for optimization performance."""

    def __init__(self):
        self.enabled = settings.ENABLE_METRICS

    def track_cache_hit(self):
        """Track semantic cache hit."""
        if self.enabled:
            cache_hits.inc()

    def track_cache_miss(self):
        """Track semantic cache miss."""
        if self.enabled:
            cache_misses.inc()

    def track_model_usage(self, model: str, provider: str):
        """Track model API call."""
        if self.enabled:
            model_usage.labels(model=model, provider=provider).inc()

    def track_token_usage(self, original: int, compressed: int, saved: int):
        """Track token usage and savings."""
        if self.enabled:
            token_usage.labels(type="original").inc(original)
            token_usage.labels(type="compressed").inc(compressed)
            token_usage.labels(type="saved").inc(saved)

    def track_optimization(self, optimization_type: str):
        """Track optimization application."""
        if self.enabled:
            optimization_applied.labels(optimization_type=optimization_type).inc()

    def track_request(self, endpoint: str, method: str):
        """Track API request."""
        if self.enabled:
            request_count.labels(endpoint=endpoint, method=method).inc()

    def track_response_time(self, endpoint: str, duration: float):
        """Track response time."""
        if self.enabled:
            response_time.labels(endpoint=endpoint).observe(duration)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary (non-Prometheus format for debugging)."""
        return {
            "cache": {
                "description": "Semantic cache performance",
                "metrics": ["cache_hits", "cache_misses"]
            },
            "models": {
                "description": "Model usage by provider",
                "metrics": ["model_usage_total"]
            },
            "tokens": {
                "description": "Token usage and compression savings",
                "metrics": ["token_usage_total"]
            },
            "optimizations": {
                "description": "Applied optimization techniques",
                "metrics": ["optimizations_applied_total"]
            },
            "performance": {
                "description": "API performance metrics",
                "metrics": ["request_count", "response_time"]
            }
        }


# Global metrics collector
metrics_collector = MetricsCollector()


class MetricsMiddleware:
    """Middleware to automatically collect request metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            endpoint = scope.get("path", "unknown")
            method = scope.get("method", "unknown")

            metrics_collector.track_request(endpoint, method)

            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = time.time() - start_time
                    metrics_collector.track_response_time(endpoint, duration)
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
