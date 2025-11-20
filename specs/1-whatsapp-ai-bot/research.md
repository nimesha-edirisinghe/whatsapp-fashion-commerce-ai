# Research: FashionImport AI Bot

**Date**: 2025-11-20
**Branch**: `1-whatsapp-ai-bot`

## Technology Decisions

### 1. Embedding Model Selection

**Decision**: OpenAI `text-embedding-3-small` (1536 dimensions)

**Rationale**:
- Best balance of cost and performance for product search
- Native integration with GPT-5 for consistent semantic understanding
- 1536 dimensions sufficient for fashion attribute similarity
- Lower latency than `text-embedding-3-large`

**Alternatives Considered**:
- `text-embedding-3-large` (3072 dim): Higher accuracy but 2x cost, overkill for fashion search
- Cohere Embed: Good but adds another API dependency
- Sentence-transformers (local): Doesn't fit Vercel serverless model

### 2. Image Analysis Approach

**Decision**: Gemini 2.0 Flash with structured JSON output

**Rationale**:
- Best multimodal performance for fashion attribute extraction
- Supports structured JSON output for reliable parsing
- Flash model balances speed and capability
- Google AI Studio API is simpler than Vertex AI

**Alternatives Considered**:
- GPT-4 Vision: Slightly better reasoning but slower and more expensive
- CLIP embeddings: Good for direct image similarity but no attribute extraction
- Custom fashion model: Too much development overhead for MVP

### 3. Vector Search Configuration

**Decision**: Supabase pgvector with IVFFlat index (100 lists)

**Rationale**:
- IVFFlat provides good balance of speed and recall for <10k products
- 100 lists optimal for expected 1000-10000 product range
- Cosine similarity matches embedding model optimization
- Native Supabase integration, no additional service

**Alternatives Considered**:
- HNSW index: Faster queries but slower inserts, better for >100k items
- Pinecone: Excellent but adds cost and complexity
- Qdrant: Self-hosted complexity doesn't fit Vercel model

### 4. Session Storage Strategy

**Decision**: Redis lists with 24h TTL, 10 message limit per conversation

**Rationale**:
- Lists provide O(1) append and efficient range queries
- 24h TTL aligns with WhatsApp messaging window
- 10 messages provides sufficient context without excessive token usage
- Upstash serverless fits Vercel deployment

**Alternatives Considered**:
- Supabase for sessions: Higher latency, 24h expiry harder to manage
- In-memory (function scope): Lost between invocations
- DynamoDB: Adds AWS dependency

### 5. Retry and Fallback Pattern

**Decision**: Single retry with 3s timeout, then graceful fallback

**Rationale**:
- 3s timeout prevents user-visible delays (total 6s worst case)
- Single retry catches transient network issues
- Fallback menu ensures user always gets response
- Matches spec's 10s response time requirement

**Implementation**:
```python
@retry(attempts=1, timeout=3.0)
async def call_external_service():
    ...

try:
    response = await call_external_service()
except (TimeoutError, ServiceError):
    response = fallback_menu_response()
```

### 6. WhatsApp Message Types

**Decision**: Use interactive messages for catalog browsing, text for Q&A

**Rationale**:
- Interactive lists support up to 10 items with sections
- Interactive buttons for quick actions (max 3)
- Text messages for detailed product info and Q&A
- Image messages for product photos (via media upload)

**Message Type Mapping**:
- Visual search results → Text with image URLs
- Catalog browse → Interactive list message
- Q&A responses → Text message
- Order status → Text message with tracking link
- Escalation → Text message with handoff notice

### 7. Language Detection

**Decision**: Use GPT-5 built-in capability with explicit instruction

**Rationale**:
- GPT-5 natively detects language from context
- System prompt instructs response in same language
- No additional API calls or libraries
- Works across all supported languages

**Alternatives Considered**:
- langdetect library: Adds dependency, less accurate on short messages
- Google Translate API: Overkill, adds cost
- WhatsApp locale header: Not always reliable

### 8. Admin API Security

**Decision**: API key authentication via X-API-Key header

**Rationale**:
- Simple, stateless authentication for n8n webhooks
- No user sessions to manage
- Key rotation straightforward
- Sufficient for internal admin endpoints

**Alternatives Considered**:
- JWT: Overkill for machine-to-machine
- OAuth2: Too complex for single admin endpoint
- IP allowlist: Hard to maintain with n8n cloud

## Best Practices Applied

### FastAPI Patterns
- Dependency injection for services
- Pydantic settings for configuration
- Background tasks for non-blocking operations
- Middleware for logging and error handling

### Supabase Patterns
- Use service role key for backend operations
- RLS policies for future multi-tenant support
- Indexes on all query fields
- JSONB for flexible metadata

### Error Handling
- Custom exception classes per service
- Sentry context enrichment
- Structured logging with correlation IDs
- User-friendly error messages in detected language

### Testing Strategy
- Contract tests mock external APIs
- Integration tests use test database
- Unit tests for business logic
- Fixtures for common test data
