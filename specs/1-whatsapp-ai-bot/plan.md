# Implementation Plan: FashionImport AI Bot

**Branch**: `1-whatsapp-ai-bot` | **Date**: 2025-11-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/1-whatsapp-ai-bot/spec.md`

## Summary

Build a WhatsApp-based AI sales and support agent for a clothing import business. The system provides visual product search (Gemini 2.0 Vision), contextual Q&A (GPT-5 + RAG), order tracking (n8n integration), and catalog browsing. Built with FastAPI on Vercel, using Supabase for data storage and vector search, with Redis session caching via Upstash.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic v2, OpenAI SDK, Google Generative AI, Supabase-py, Redis (aioredis)
**Storage**: Supabase PostgreSQL + pgvector, Supabase Storage, Upstash Redis
**Testing**: pytest, pytest-asyncio
**Target Platform**: Vercel Serverless Functions (Linux)
**Project Type**: Single API backend (no frontend)
**Performance Goals**: <10s visual search response, <5s text response, 100 concurrent conversations
**Constraints**: WhatsApp 24h messaging window, 3s retry timeout for external services
**Scale/Scope**: Initial launch with ~1000 products, scaling to 10k+ products

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation |
|-----------|--------|----------------|
| I. Service-Oriented Architecture | ✅ PASS | Separate services for AI, Database, WhatsApp, Automation |
| II. Strict Type Safety | ✅ PASS | Pydantic v2 models for all data, complete type hints |
| III. Async-First Design | ✅ PASS | All endpoints async, async DB/Redis clients |
| IV. WhatsApp API Compliance | ✅ PASS | Webhook verification, 24h window handling, template messages |
| V. Graceful Degradation | ✅ PASS | Retry once + fallback to rule-based menu |
| VI. Security-First | ✅ PASS | Environment variables, webhook signature verification, parameterized queries |
| VII. Observability | ✅ PASS | Sentry integration, structured logging, conversation tracing |

## Project Structure

### Documentation (this feature)

```text
specs/1-whatsapp-ai-bot/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py                    # FastAPI application entry point
├── config.py                  # Settings and environment variables
│
├── api/
│   ├── __init__.py
│   ├── webhook.py             # POST /webhook - WhatsApp webhook handler
│   ├── admin.py               # POST /admin/sync-catalog - n8n catalog sync
│   └── health.py              # GET /health - Health check endpoint
│
├── models/
│   ├── __init__.py
│   ├── whatsapp.py            # WhatsApp API request/response models
│   ├── product.py             # Product entity models
│   ├── order.py               # Order entity models
│   ├── conversation.py        # Conversation/session models
│   └── catalog.py             # Catalog sync models
│
├── services/
│   ├── __init__.py
│   ├── whatsapp_service.py    # WhatsApp Cloud API client
│   ├── ai_service.py          # GPT-5 text generation
│   ├── vision_service.py      # Gemini 2.0 Vision analysis
│   ├── rag_service.py         # RAG pipeline (embeddings + search)
│   ├── product_service.py     # Product CRUD and search
│   ├── order_service.py       # Order status retrieval
│   ├── session_service.py     # Redis session management
│   └── escalation_service.py  # Human agent escalation via n8n
│
├── core/
│   ├── __init__.py
│   ├── database.py            # Supabase client initialization
│   ├── redis.py               # Upstash Redis client
│   ├── openai_client.py       # OpenAI client initialization
│   ├── gemini_client.py       # Google AI client initialization
│   ├── logging.py             # Structured logging setup
│   └── exceptions.py          # Custom exception classes
│
└── utils/
    ├── __init__.py
    ├── language.py            # Language detection
    ├── retry.py               # Retry decorator with timeout
    └── message_builder.py     # WhatsApp message formatting

tests/
├── __init__.py
├── conftest.py                # Pytest fixtures
├── contract/
│   ├── test_whatsapp_api.py   # WhatsApp API contract tests
│   ├── test_openai_api.py     # OpenAI API contract tests
│   └── test_supabase_api.py   # Supabase API contract tests
├── integration/
│   ├── test_webhook_flow.py   # End-to-end webhook tests
│   ├── test_visual_search.py  # Image processing flow tests
│   └── test_rag_pipeline.py   # RAG query flow tests
└── unit/
    ├── test_services/         # Unit tests for each service
    └── test_models/           # Model validation tests

# Root files
.env.example                   # Environment variable template
.gitignore
Dockerfile                     # Local development container
docker-compose.yml             # Local dev with Redis
requirements.txt               # Python dependencies
pyproject.toml                 # Project metadata and tooling
vercel.json                    # Vercel deployment configuration
```

**Structure Decision**: Single project structure chosen as this is a backend-only API service with no frontend. The `app/` directory follows FastAPI conventions with clear separation between API routes, business services, data models, and core infrastructure.

## Database Schema (Supabase)

### Products Table

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    supplier_url TEXT,
    image_urls TEXT[] NOT NULL,
    sizes TEXT[] NOT NULL,  -- ['S', 'M', 'L', 'XL'] or ['6', '8', '10']
    colors TEXT[] NOT NULL,
    inventory_count INTEGER DEFAULT 0,
    category VARCHAR(100),
    tags TEXT[],
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search
CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Index for category/tag filtering
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_is_active ON products(is_active);
```

### Orders Table

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(50) UNIQUE NOT NULL,  -- External order ID (e.g., ORD-12345)
    customer_phone VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- Processing, Shipped, Delivered, Cancelled
    tracking_number VARCHAR(100),
    carrier VARCHAR(100),
    estimated_delivery DATE,
    items JSONB NOT NULL,  -- [{product_id, name, quantity, price}]
    total_amount DECIMAL(10, 2) NOT NULL,
    shipping_address JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for order lookup
CREATE INDEX idx_orders_order_id ON orders(order_id);
CREATE INDEX idx_orders_customer_phone ON orders(customer_phone);
```

### Conversations Table (Analytics)

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_phone VARCHAR(20) NOT NULL,
    message_type VARCHAR(20) NOT NULL,  -- text, image, interactive
    direction VARCHAR(10) NOT NULL,     -- inbound, outbound
    content TEXT,
    intent VARCHAR(50),                 -- visual_search, qa, order_tracking, browse
    confidence_score DECIMAL(3, 2),
    response_time_ms INTEGER,
    escalated BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX idx_conversations_customer ON conversations(customer_phone);
CREATE INDEX idx_conversations_intent ON conversations(intent);
CREATE INDEX idx_conversations_created ON conversations(created_at);
```

### Knowledge Base Table (RAG)

```sql
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type VARCHAR(50) NOT NULL,  -- policy, faq, product_info
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

## API Structure (FastAPI)

### POST /webhook

Main entry point for WhatsApp Cloud API. Handles both verification (GET) and message events (POST).

```python
@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge")
) -> PlainTextResponse:
    """Verify WhatsApp webhook subscription."""

@router.post("/webhook")
async def handle_webhook(
    request: Request,
    payload: WhatsAppWebhookPayload
) -> dict:
    """Process incoming WhatsApp messages (text, image, interactive)."""
```

### POST /admin/sync-catalog

Endpoint triggered by n8n to sync products from supplier sheets.

```python
@router.post("/admin/sync-catalog")
async def sync_catalog(
    payload: CatalogSyncPayload,
    api_key: str = Header(..., alias="X-API-Key")
) -> CatalogSyncResponse:
    """
    Sync product catalog from n8n workflow.
    - Upsert products with embeddings
    - Update inventory counts
    - Deactivate removed products
    """
```

### GET /health

Health check for Vercel and monitoring.

```python
@router.get("/health")
async def health_check() -> HealthResponse:
    """
    Check system health:
    - Database connectivity
    - Redis connectivity
    - External API availability
    """
```

## Integration Logic

### WhatsApp Cloud API Authentication

```python
# app/services/whatsapp_service.py
class WhatsAppService:
    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    async def send_message(self, to: str, message: WhatsAppMessage) -> dict:
        """Send message via WhatsApp Cloud API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{self.phone_number_id}/messages",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json=message.dict()
            )
            return response.json()

    async def download_media(self, media_id: str) -> bytes:
        """Download media file from WhatsApp servers."""
        # First get media URL, then download content
```

### OpenAI Client Initialization

```python
# app/core/openai_client.py
from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_response(
    messages: list[dict],
    model: str = "gpt-5"
) -> str:
    """Generate text response with GPT-5."""
    response = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content

async def create_embedding(text: str) -> list[float]:
    """Create embedding for RAG search."""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
```

### Google Gemini Client Initialization

```python
# app/core/gemini_client.py
import google.generativeai as genai

genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')

async def analyze_clothing_image(image_bytes: bytes) -> ClothingAttributes:
    """
    Analyze clothing image to extract attributes.
    Returns: garment_type, colors, patterns, style keywords
    """
    response = await vision_model.generate_content_async([
        "Analyze this clothing image and extract: garment type, colors, patterns, and style keywords. "
        "Return as JSON: {garment_type, colors: [], patterns: [], style_keywords: []}",
        {"mime_type": "image/jpeg", "data": image_bytes}
    ])
    return ClothingAttributes.parse_raw(response.text)
```

### Upstash Redis Connection

```python
# app/core/redis.py
from redis.asyncio import Redis

redis_client = Redis.from_url(
    settings.UPSTASH_REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

class SessionService:
    async def get_conversation_history(self, phone: str) -> list[dict]:
        """Get last 10 messages for context."""
        key = f"session:{phone}:messages"
        messages = await redis_client.lrange(key, -10, -1)
        return [json.loads(m) for m in messages]

    async def add_message(self, phone: str, message: dict) -> None:
        """Add message to conversation history."""
        key = f"session:{phone}:messages"
        await redis_client.rpush(key, json.dumps(message))
        await redis_client.ltrim(key, -10, -1)  # Keep only last 10
        await redis_client.expire(key, 86400)   # 24h expiry
```

## Development Phases

### Phase 1: Foundation (Week 1-2)
Scaffold FastAPI + Supabase connection + Basic Webhook Verification

- [ ] Initialize project structure and dependencies
- [ ] Configure environment variables and settings
- [ ] Set up Supabase database with initial schema
- [ ] Implement WhatsApp webhook verification (GET /webhook)
- [ ] Implement basic webhook handler (POST /webhook) - echo messages
- [ ] Set up Upstash Redis connection
- [ ] Configure Sentry for error tracking
- [ ] Create health check endpoint
- [ ] Write initial contract tests

### Phase 2: Text RAG Pipeline (Week 3-4)
Implement Text RAG pipeline (GPT-5 + Vector Search)

- [ ] Implement OpenAI client with embeddings
- [ ] Create product and knowledge base embedding pipeline
- [ ] Implement vector similarity search in Supabase
- [ ] Build RAG service (retrieve + generate)
- [ ] Implement session service with conversation history
- [ ] Add language detection for multilingual responses
- [ ] Implement graceful degradation (fallback menu)
- [ ] Create Q&A integration tests

### Phase 3: Vision Pipeline (Week 5-6)
Implement Vision pipeline (Gemini 2.0 + Image processing)

- [ ] Implement Gemini client for image analysis
- [ ] Build image download from WhatsApp media
- [ ] Create clothing attribute extraction
- [ ] Implement visual similarity search
- [ ] Build product recommendation formatter
- [ ] Add non-clothing image filtering
- [ ] Create visual search integration tests

### Phase 4: n8n Integration (Week 7)
Add n8n integration for Order Status and Catalog Sync

- [ ] Implement order tracking service
- [ ] Create admin catalog sync endpoint
- [ ] Build escalation service for human handoff
- [ ] Set up n8n webhooks for notifications
- [ ] Implement order status message formatting
- [ ] Create integration tests for n8n flows

### Phase 5: Deployment & Polish (Week 8)
Deployment to Vercel & Dockerizing for local dev

- [ ] Create Dockerfile for local development
- [ ] Set up docker-compose with Redis
- [ ] Configure Vercel deployment
- [ ] Set up GitHub Actions CI/CD
- [ ] Performance testing and optimization
- [ ] Documentation and quickstart guide
- [ ] Security audit (webhook signatures, rate limiting)

## Complexity Tracking

> No constitution violations requiring justification.

## Environment Variables

```bash
# WhatsApp Cloud API
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=

# OpenAI
OPENAI_API_KEY=

# Google AI
GOOGLE_AI_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Upstash Redis
UPSTASH_REDIS_URL=

# Sentry
SENTRY_DSN=

# Admin
ADMIN_API_KEY=
```
