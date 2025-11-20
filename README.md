# FashionImport AI Bot

WhatsApp-based AI sales and support agent for clothing import business.

## Features

- **Visual Product Search**: Send clothing photos to find similar items
- **Q&A Support**: Natural language questions with RAG-powered answers
- **Order Tracking**: Check order status with order ID
- **Catalog Browsing**: Browse products via trigger phrases ("New Arrivals", "Trending", "Sale")

## Tech Stack

- **Backend**: FastAPI + Python 3.11
- **AI**: GPT-4 (text), Gemini 2.0 Vision (images), OpenAI Embeddings
- **Database**: Supabase PostgreSQL + pgvector
- **Cache**: Redis (Upstash)
- **Messaging**: WhatsApp Cloud API
- **Automation**: n8n (catalog sync, escalation)
- **Hosting**: Vercel

## Setup

### Prerequisites

- Python 3.11+
- Redis (local or Upstash)
- Supabase project
- WhatsApp Business API access
- OpenAI API key
- Google AI (Gemini) API key

### Local Development

1. Clone the repository:
```bash
git clone <repo-url>
cd whatsapp-fashion-commerce-ai
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Configure environment variables in `.env`

6. Run database migrations:
```bash
# Apply migrations in Supabase dashboard or CLI
```

7. Start the server:
```bash
uvicorn app.main:app --reload
```

### Docker Development

```bash
docker-compose up
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Cloud API token | Yes |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID | Yes |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification token | Yes |
| `WHATSAPP_APP_SECRET` | App secret for signature verification | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon/service key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `GEMINI_API_KEY` | Google AI API key | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `SENTRY_DSN` | Sentry DSN for error tracking | No |
| `ADMIN_API_KEY` | API key for admin endpoints | Yes |
| `N8N_WEBHOOK_URL` | n8n webhook for escalation | No |

## API Endpoints

### WhatsApp
- `GET /webhook` - Webhook verification
- `POST /webhook` - Handle incoming messages

### Admin
- `POST /admin/sync-catalog` - Sync product catalog
- `GET /admin/catalog/stats` - Get catalog statistics

### System
- `GET /health` - Health check
- `GET /` - Root endpoint

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_visual_search.py -v
```

## Linting & Type Checking

```bash
# Lint
ruff check app/ tests/

# Type check
mypy app/ --ignore-missing-imports
```

## Deployment

### Vercel

1. Connect repository to Vercel
2. Configure environment variables
3. Deploy

### Manual

1. Build Docker image:
```bash
docker build -t fashionimport-bot .
```

2. Run container:
```bash
docker run -p 8000:8000 --env-file .env fashionimport-bot
```

## Architecture

```
app/
├── api/          # FastAPI routers
├── core/         # Database, Redis, AI clients
├── models/       # Pydantic models
├── services/     # Business logic
└── utils/        # Helpers and utilities
```

## License

Proprietary
