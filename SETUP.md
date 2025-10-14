# Setup Guide

Complete setup guide for Mock Interviews AI API.

## Prerequisites

- Python 3.11 or higher
- Redis (for semantic caching)
- Git

## Installation

### 1. Clone and Setup Virtual Environment

```bash
cd /Users/mahadev/Project/Indie/mockinterviews

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Redis

**macOS (Homebrew)**:
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Windows**:
- Download Redis from: https://github.com/microsoftarchive/redis/releases
- Or use Docker (see Docker setup below)

**Verify Redis is running**:
```bash
redis-cli ping
# Should return: PONG
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

**Required configuration in `.env`**:

```bash
# AI Provider (choose one: anthropic or openai)
AI_PROVIDER=anthropic

# Anthropic API Key (get from: https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx

# OpenAI API Key (get from: https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx

# Redis URL
REDIS_URL=redis://localhost:6379

# Database
DATABASE_URL=sqlite:///./interviews.db

# Enable all optimizations
ENABLE_SEMANTIC_CACHE=true
ENABLE_MODEL_ROUTING=true
ENABLE_PROMPT_COMPRESSION=true
ENABLE_SESSION_SUMMARIZATION=true
ENABLE_FALLBACK=true
```

### 5. Initialize Database

The database will be created automatically on first run. To manually initialize:

```bash
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## Running the API

### Development Mode

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the API with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

**API Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Production Mode

```bash
# Install additional production dependencies
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Docker Setup (Alternative)

If you prefer Docker, you can run everything with Docker Compose:

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This will start:
- Redis on port 6379
- API on port 8000

## Testing the API

### 1. Check Health

```bash
curl http://localhost:8000/api/v1/metrics/health
```

### 2. Run Test Client

```bash
# Make sure API is running first
python test_client.py
```

### 3. Manual API Testing

**Create a session**:
```bash
curl -X POST "http://localhost:8000/api/v1/interviews/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_type": "technical",
    "role": "Software Engineer",
    "level": "senior",
    "focus_areas": ["algorithms", "data structures"]
  }'
```

**Send a message** (replace SESSION_ID):
```bash
curl -X POST "http://localhost:8000/api/v1/interviews/sessions/SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I would use a hash map to solve this problem"
  }'
```

**End session and get feedback**:
```bash
curl -X POST "http://localhost:8000/api/v1/interviews/sessions/SESSION_ID/end"
```

## Troubleshooting

### Redis Connection Error

**Error**: `ConnectionError: Error connecting to Redis`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# If not running:
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### API Key Error

**Error**: `AuthenticationError: Invalid API key`

**Solution**:
- Verify your API key in `.env`
- Make sure there are no extra spaces or quotes
- Check that the key is valid in your provider's console

### Import Error

**Error**: `ModuleNotFoundError: No module named 'xyz'`

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install package-name
```

### Database Lock Error

**Error**: `sqlite3.OperationalError: database is locked`

**Solution**:
```bash
# For production, use PostgreSQL instead of SQLite
# Update .env:
DATABASE_URL=postgresql://user:password@localhost/mockinterviews
```

### Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 PID

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

## Optimization Configuration

### Disable Specific Optimizations

Edit `.env` to disable optimizations if needed:

```bash
# Disable semantic caching (if Redis not available)
ENABLE_SEMANTIC_CACHE=false

# Disable model routing (always use large model)
ENABLE_MODEL_ROUTING=false

# Disable prompt compression
ENABLE_PROMPT_COMPRESSION=false

# Disable session summarization
ENABLE_SESSION_SUMMARIZATION=false
```

### Tune Performance Parameters

```bash
# Semantic Cache
CACHE_SIMILARITY_THRESHOLD=0.95  # Higher = stricter matching
CACHE_TTL=3600                   # Cache expiry in seconds

# Model Routing
ROUTING_COMPLEXITY_THRESHOLD=100  # Tokens threshold for large model

# Prompt Compression
MAX_CONTEXT_TOKENS=8000          # Max tokens before compression
COMPRESSION_RATIO=0.7            # Keep 70% of content

# Session Summarization
SUMMARIZATION_TRIGGER=10         # Summarize after N messages
KEEP_RECENT_MESSAGES=4           # Keep N recent messages uncompressed
```

## Monitoring

### View Prometheus Metrics

```bash
curl http://localhost:8000/api/v1/metrics
```

### Key Metrics to Monitor

- `interview_requests_total` - Total API requests
- `interview_response_time_seconds` - Response times
- `semantic_cache_hits_total` - Cache efficiency
- `model_usage_total` - Model distribution
- `token_usage_total` - Token usage and savings

### Integration with Monitoring Tools

The API exposes Prometheus-compatible metrics that can be scraped by:
- Prometheus + Grafana
- Datadog
- New Relic
- AWS CloudWatch

## Next Steps

1. Explore the API documentation at http://localhost:8000/docs
2. Review `ARCHITECTURE.md` to understand optimization strategies
3. Run the test client to see optimizations in action
4. Customize interview prompts in `app/services/interview_service.py`
5. Deploy to production (see deployment guides)

## Support

For issues and questions:
- Check `ARCHITECTURE.md` for technical details
- Review code comments in service files
- Open an issue on GitHub (if applicable)
