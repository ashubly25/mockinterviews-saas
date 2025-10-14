from fastapi import APIRouter
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from app.core.config import settings

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Prometheus metrics
request_count = Counter(
    'interview_requests_total',
    'Total interview API requests',
    ['endpoint', 'method']
)

response_time = Histogram(
    'interview_response_time_seconds',
    'Response time for interview requests',
    ['endpoint']
)

cache_hits = Counter(
    'semantic_cache_hits_total',
    'Total semantic cache hits'
)

cache_misses = Counter(
    'semantic_cache_misses_total',
    'Total semantic cache misses'
)

model_usage = Counter(
    'model_usage_total',
    'Total model API calls',
    ['model', 'provider']
)

token_usage = Counter(
    'token_usage_total',
    'Total tokens used',
    ['type']  # original, compressed, saved
)

optimization_applied = Counter(
    'optimizations_applied_total',
    'Total optimizations applied',
    ['optimization_type']
)


@router.get("/")
async def metrics():
    """
    Expose Prometheus metrics.

    Metrics include:
    - Request counts and response times
    - Cache hit/miss rates
    - Model usage statistics
    - Token usage and savings
    - Optimization application counts
    """
    if not settings.ENABLE_METRICS:
        return {"message": "Metrics disabled"}

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "optimizations": {
            "semantic_caching": settings.ENABLE_SEMANTIC_CACHE,
            "model_routing": settings.ENABLE_MODEL_ROUTING,
            "prompt_compression": settings.ENABLE_PROMPT_COMPRESSION,
            "session_summarization": settings.ENABLE_SESSION_SUMMARIZATION
        }
    }
