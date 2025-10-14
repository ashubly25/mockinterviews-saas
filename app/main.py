from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api import interviews, metrics

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI-powered mock interview platform with advanced optimizations",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(interviews.router, prefix=settings.API_V1_PREFIX)
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Mock Interviews AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "features": {
            "semantic_caching": settings.ENABLE_SEMANTIC_CACHE,
            "model_routing": settings.ENABLE_MODEL_ROUTING,
            "prompt_compression": settings.ENABLE_PROMPT_COMPRESSION,
            "session_summarization": settings.ENABLE_SESSION_SUMMARIZATION
        },
        "endpoints": {
            "create_session": f"{settings.API_V1_PREFIX}/interviews/sessions",
            "send_message": f"{settings.API_V1_PREFIX}/interviews/sessions/{{session_id}}/messages",
            "end_session": f"{settings.API_V1_PREFIX}/interviews/sessions/{{session_id}}/end",
            "metrics": f"{settings.API_V1_PREFIX}/metrics",
            "health": f"{settings.API_V1_PREFIX}/metrics/health"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"🚀 Starting {settings.PROJECT_NAME}")
    print(f"📊 Optimizations enabled:")
    print(f"   - Semantic Caching: {settings.ENABLE_SEMANTIC_CACHE}")
    print(f"   - Model Routing: {settings.ENABLE_MODEL_ROUTING}")
    print(f"   - Prompt Compression: {settings.ENABLE_PROMPT_COMPRESSION}")
    print(f"   - Session Summarization: {settings.ENABLE_SESSION_SUMMARIZATION}")
    print(f"📡 API docs available at: /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 Shutting down gracefully...")
