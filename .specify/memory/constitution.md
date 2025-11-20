<!--
Sync Impact Report
==================
Version change: 0.0.0 → 1.0.0
Bump rationale: Initial constitution creation (MAJOR - first adoption)

Modified principles: N/A (initial creation)
Added sections: Core Principles (7), Technology Stack, Development Workflow
Removed sections: None

Templates requiring updates:
- .specify/templates/plan-template.md ✅ No changes required (generic template)
- .specify/templates/spec-template.md ✅ No changes required (generic template)
- .specify/templates/tasks-template.md ✅ No changes required (generic template)

Follow-up TODOs: None
-->

# WhatsApp Fashion Commerce AI Constitution

## Core Principles

### I. Service-Oriented Architecture

All code MUST be organized into clearly separated service layers:
- **AI Services**: GPT-5 for core logic, Gemini 2.0 Vision for image analysis
- **Database Services**: Supabase PostgreSQL CRUD operations, pgvector RAG queries
- **WhatsApp Services**: Webhook handling, message routing, 24h window compliance
- **Automation Services**: n8n workflow integration for order sync

Services MUST NOT directly depend on each other's implementations; communicate through defined interfaces.

### II. Strict Type Safety (NON-NEGOTIABLE)

- All Python code MUST use complete type hints (parameters, return types, class attributes)
- Pydantic v2 models MUST be used for all data validation
- No `Any` types unless explicitly justified and documented
- Type checking MUST pass before merge

### III. Async-First Design

- All I/O operations MUST use async/await syntax
- FastAPI endpoints MUST be async
- Database operations MUST use async drivers (asyncpg via Supabase)
- Redis operations MUST use async client (Upstash)

### IV. WhatsApp API Compliance

- MUST adhere to Meta's 24-hour messaging window rules
- Session messages vs template messages MUST be correctly categorized
- Webhook verification MUST follow Meta's security requirements
- Message types (text, image, interactive) MUST use correct API formats

### V. Graceful Degradation

- If AI services (GPT-5/Gemini) fail, system MUST fallback to rule-based menu
- If RAG search fails, system MUST fallback to keyword search or static responses
- If external services timeout, system MUST return user-friendly error messages
- All failures MUST be logged to Sentry with full context

### VI. Security-First

- API keys MUST NEVER appear in code; use `.env` locally and Vercel Environment Variables in production
- All user inputs MUST be validated before processing
- WhatsApp webhook signatures MUST be verified
- Database queries MUST use parameterized statements (SQLAlchemy/Supabase client)

### VII. Observability

- All service operations MUST emit structured logs
- Sentry MUST capture all unhandled exceptions with request context
- Performance metrics MUST be tracked for AI response times
- User conversation flows MUST be traceable for debugging

## Technology Stack

**Interface**: WhatsApp Cloud API (Meta)
**Backend**: FastAPI (Python 3.11+) with Pydantic v2
**AI Layer**:
- Core Logic: GPT-5 (OpenAI API)
- Vision/Multimodal: Gemini 2.0 Vision (Google AI Studio API)
**Database**: Supabase PostgreSQL + pgvector for RAG
**Storage**: Supabase Storage (product catalog images)
**Automation**: n8n (order sync, backend workflows)
**Caching**: Redis via Upstash (serverless)
**Hosting**: Vercel (serverless functions)
**Monitoring**: Sentry
**CI/CD**: Docker + GitHub Actions

## Development Workflow

### Code Standards
- Language: English for all code and comments
- Bot responses: Language determined by user input (multilingual support)
- All PRs MUST pass type checking, linting, and tests
- Commits MUST follow conventional commit format

### Testing Requirements
- Unit tests for all service methods
- Integration tests for WhatsApp webhook flows
- Contract tests for external API integrations (OpenAI, Google AI, Supabase)

### Deployment Pipeline
1. PR triggers GitHub Actions
2. Docker build and test
3. Deploy to Vercel on merge to main
4. Sentry release tracking

## Governance

This constitution supersedes all other development practices for this project.

**Amendment Process**:
1. Propose change with rationale
2. Document impact on existing code
3. Update constitution version per semantic versioning
4. Migrate existing code if required

**Compliance Review**:
- All PRs MUST verify adherence to principles
- Architecture decisions MUST reference applicable principles
- Exceptions MUST be documented in Complexity Tracking table

**Version**: 1.0.0 | **Ratified**: 2025-11-20 | **Last Amended**: 2025-11-20
