# Quickstart: FashionImport AI Bot

**Date**: 2025-11-20
**Branch**: `1-whatsapp-ai-bot`

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for local development)
- WhatsApp Business Account with Cloud API access
- Supabase project
- Upstash Redis account
- OpenAI API key
- Google AI Studio API key

## Quick Setup

### 1. Clone and Install

```bash
git clone <repository>
cd whatsapp-fashion-commerce-ai
git checkout 1-whatsapp-ai-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# WhatsApp Cloud API
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_APP_SECRET=your_app_secret

# OpenAI
OPENAI_API_KEY=sk-...

# Google AI
GOOGLE_AI_API_KEY=AIza...

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Upstash Redis
UPSTASH_REDIS_URL=rediss://...

# Sentry (optional for local)
SENTRY_DSN=

# Admin
ADMIN_API_KEY=your_secure_admin_key
```

### 3. Database Setup

Run these SQL commands in Supabase SQL editor:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables (see data-model.md for full schema)
-- Products, Orders, Conversations, KnowledgeBase
```

Or use the migration script:
```bash
python -m app.scripts.setup_database
```

### 4. Local Development

**Option A: Direct Python**
```bash
uvicorn app.main:app --reload --port 8000
```

**Option B: Docker Compose** (includes Redis)
```bash
docker-compose up --build
```

### 5. Webhook Tunnel (for WhatsApp testing)

Use ngrok to expose local server:
```bash
ngrok http 8000
```

Configure webhook in Meta Developer Console:
- Webhook URL: `https://your-ngrok-url.ngrok.io/webhook`
- Verify Token: Same as `WHATSAPP_VERIFY_TOKEN` in `.env`
- Subscribe to: `messages`

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

### Manual Testing

**Health Check**
```bash
curl http://localhost:8000/health
```

**Webhook Verification**
```bash
curl "http://localhost:8000/webhook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=test123"
```

**Simulate Text Message**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "1234567890",
            "type": "text",
            "text": {"body": "Do you have summer dresses?"}
          }]
        }
      }]
    }]
  }'
```

## Project Structure

```
app/
├── main.py           # FastAPI app
├── config.py         # Settings
├── api/              # Route handlers
├── models/           # Pydantic models
├── services/         # Business logic
├── core/             # Clients and infra
└── utils/            # Helpers

tests/
├── contract/         # External API mocks
├── integration/      # End-to-end flows
└── unit/             # Service tests
```

## Common Tasks

### Add a Product

```python
from app.services.product_service import ProductService

service = ProductService()
await service.create_product({
    "name": "Summer Dress",
    "price": 29.99,
    "image_urls": ["https://..."],
    "sizes": ["S", "M", "L"],
    "colors": ["Blue", "White"],
    "category": "dress"
})
```

### Sync Catalog via n8n

```bash
curl -X POST http://localhost:8000/admin/sync-catalog \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_admin_key" \
  -d '{
    "products": [
      {"name": "...", "price": 29.99, ...}
    ]
  }'
```

### Check Redis Sessions

```bash
redis-cli -u $UPSTASH_REDIS_URL

# List session keys
KEYS session:*

# Get conversation history
LRANGE session:1234567890:messages 0 -1
```

## Deployment

### Vercel

1. Push to main branch
2. GitHub Actions runs tests
3. Deploy to Vercel on success

Or manual deploy:
```bash
vercel --prod
```

### Environment Variables

Set in Vercel project settings:
- All variables from `.env`
- No need for `SENTRY_DSN` locally

## Troubleshooting

### Webhook Not Receiving Messages

1. Check ngrok is running and URL is correct
2. Verify token matches in Meta console and `.env`
3. Check webhook subscriptions include `messages`
4. View ngrok dashboard for incoming requests

### AI Response Errors

1. Check API keys are valid
2. Verify Sentry for error details
3. Check Redis for session data
4. Review logs for timeout errors

### Database Connection Issues

1. Verify Supabase URL and keys
2. Check pgvector extension is enabled
3. Ensure tables exist
4. Check for RLS policy issues (use service role key)

## Next Steps

1. Seed product catalog
2. Add knowledge base content (FAQs, policies)
3. Configure n8n workflows
4. Test all user stories
5. Deploy to staging
