# Mock Interviews AI Agent API

An AI-powered mock interview platform that provides realistic interview experiences with intelligent evaluation and feedback.

## Features

- **AI-Powered Interviews**: Interactive interview sessions with AI interviewer
- **Multiple Interview Types**: Technical, behavioral, system design, and more
- **Real-time Feedback**: Instant evaluation and detailed feedback
- **Session Management**: Track and review past interview sessions
- **RESTful API**: Easy integration with any frontend application
- **Extensible**: Support for multiple AI providers (Claude, OpenAI)

## Architecture

```
mockinterviews/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Configuration and settings
│   ├── models/           # Database models
│   ├── services/         # Business logic
│   └── schemas/          # Pydantic schemas
├── tests/                # Test suite
└── requirements.txt      # Dependencies
```

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Run the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Create Interview Session
```bash
POST /api/v1/interviews/sessions
{
  "interview_type": "technical",
  "role": "Software Engineer",
  "level": "senior",
  "focus_areas": ["algorithms", "system design"]
}
```

### Send Message
```bash
POST /api/v1/interviews/sessions/{session_id}/messages
{
  "content": "I would use a hash map to solve this problem..."
}
```

### Get Feedback
```bash
GET /api/v1/interviews/sessions/{session_id}/feedback
```

### End Session
```bash
POST /api/v1/interviews/sessions/{session_id}/end
```

## Environment Variables

```
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=sqlite:///./interviews.db
AI_PROVIDER=anthropic  # or openai
```

## License

MIT
