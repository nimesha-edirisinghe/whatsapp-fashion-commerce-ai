# Tasks: FashionImport AI Bot

**Input**: Design documents from `/specs/1-whatsapp-ai-bot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as this is a production system requiring comprehensive testing per constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `app/`, `tests/` at repository root
- Paths shown below follow the plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan.md (app/, tests/, etc.)
- [x] T002 Create pyproject.toml with project metadata and tool configuration
- [x] T003 [P] Create requirements.txt with all dependencies (fastapi, pydantic, openai, google-generativeai, supabase, redis, httpx, sentry-sdk, pytest, pytest-asyncio)
- [x] T004 [P] Create .env.example with all environment variable placeholders
- [x] T005 [P] Create .gitignore for Python project
- [x] T006 Create app/config.py with Pydantic Settings for environment variables
- [x] T007 Create app/__init__.py and all package __init__.py files
- [x] T008 [P] Create app/core/exceptions.py with custom exception classes (ServiceError, ValidationError, ExternalAPIError)
- [x] T009 [P] Create app/core/logging.py with structured logging setup and Sentry integration
- [x] T010 Create app/main.py with FastAPI application, CORS, and router includes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T011 Create app/core/database.py with async Supabase client initialization
- [x] T012 [P] Create app/core/redis.py with async Upstash Redis client
- [x] T013 [P] Create app/core/openai_client.py with AsyncOpenAI client and embedding function
- [x] T014 [P] Create app/core/gemini_client.py with Google AI client configuration
- [x] T015 Create app/models/whatsapp.py with WhatsAppWebhookPayload, WhatsAppMessage, and response models (Pydantic v2)
- [x] T016 [P] Create app/models/product.py with Product, ProductInput, ProductSearchResult models
- [x] T017 [P] Create app/models/conversation.py with Conversation, SessionContext models
- [x] T018 Create app/utils/retry.py with async retry decorator (1 retry, 3s timeout)
- [x] T019 [P] Create app/utils/message_builder.py with WhatsApp message formatting helpers (text, image, list, buttons)
- [x] T020 Create app/services/whatsapp_service.py with send_message and download_media methods
- [x] T021 Create app/api/webhook.py with GET /webhook verification endpoint
- [x] T022 Create app/api/health.py with GET /health endpoint checking DB, Redis connectivity
- [x] T023 Create SQL migration script for Supabase tables (products, orders, conversations, knowledge_base with pgvector)
- [x] T024 Create tests/conftest.py with pytest fixtures for test database, mock clients, and test data
- [x] T025 [P] Create tests/contract/test_whatsapp_api.py with WhatsApp API contract tests
- [x] T026 [P] Create tests/contract/test_supabase_api.py with Supabase connection contract tests

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Visual Product Search (Priority: P1) 🎯 MVP

**Goal**: Enable customers to upload clothing photos and receive similar product matches from inventory

**Independent Test**: Send a clothing image via webhook and verify bot returns 3-5 matching products with images, names, and prices within 10 seconds

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T027 [P] [US1] Create tests/integration/test_visual_search.py with image upload flow test
- [x] T028 [P] [US1] Create tests/unit/test_services/test_vision_service.py with clothing attribute extraction tests
- [x] T029 [P] [US1] Create tests/contract/test_openai_api.py with embedding API contract tests

### Implementation for User Story 1

- [x] T030 [US1] Implement app/services/vision_service.py with analyze_clothing_image using Gemini 2.0
- [x] T031 [US1] Create app/models/vision.py with ClothingAttributes model (garment_type, colors, patterns, style_keywords)
- [x] T032 [US1] Implement app/services/product_service.py with vector similarity search for products
- [x] T033 [US1] Add image message handling to app/api/webhook.py POST handler
- [x] T034 [US1] Implement media download in app/services/whatsapp_service.py download_media method
- [x] T035 [US1] Add non-clothing image detection and polite rejection in vision_service.py
- [x] T036 [US1] Implement product result formatting in app/utils/message_builder.py for visual search results
- [x] T037 [US1] Add graceful degradation fallback when vision/search fails
- [x] T038 [US1] Add conversation logging for visual_search intent in app/services/conversation_service.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Q&A Support with Context (Priority: P2)

**Goal**: Enable customers to ask natural language questions and receive contextual answers using RAG

**Independent Test**: Ask product questions with follow-ups and verify accurate, contextual responses based on conversation history

### Tests for User Story 2

- [x] T039 [P] [US2] Create tests/integration/test_rag_pipeline.py with Q&A flow test including context
- [x] T040 [P] [US2] Create tests/unit/test_services/test_rag_service.py with embedding and search tests
- [x] T041 [P] [US2] Create tests/unit/test_services/test_session_service.py with conversation history tests

### Implementation for User Story 2

- [x] T042 [US2] Implement app/services/session_service.py with Redis conversation history (last 10 messages, 24h TTL)
- [x] T043 [US2] Implement app/services/rag_service.py with create_embedding and search_knowledge_base
- [x] T044 [US2] Implement app/services/ai_service.py with generate_response using GPT-5 and retrieved context
- [x] T045 [US2] Create app/utils/language.py with language detection from message content
- [x] T046 [US2] Add text message handling to app/api/webhook.py POST handler with intent detection
- [x] T047 [US2] Implement context retrieval from session in ai_service.py for contextual responses
- [x] T048 [US2] Add non-clothing query filtering with polite redirect in ai_service.py
- [x] T049 [US2] Implement graceful degradation to rule-based menu when AI fails
- [x] T050 [US2] Create app/models/knowledge_base.py with KnowledgeBaseEntry model
- [x] T051 [US2] Add conversation logging for qa intent

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Order Tracking (Priority: P3)

**Goal**: Enable customers to check order status using their order ID

**Independent Test**: Send an order ID and verify bot returns correct status, tracking number, and estimated delivery

### Tests for User Story 3

- [x] T052 [P] [US3] Create tests/integration/test_order_tracking.py with order lookup flow test
- [x] T053 [P] [US3] Create tests/unit/test_services/test_order_service.py with order retrieval tests

### Implementation for User Story 3

- [x] T054 [US3] Create app/models/order.py with Order, OrderItem, OrderStatus models
- [x] T055 [US3] Implement app/services/order_service.py with get_order_by_id from Supabase
- [x] T056 [US3] Add order ID detection and intent routing in webhook handler
- [x] T057 [US3] Implement order status message formatting in message_builder.py
- [x] T058 [US3] Add invalid order ID handling with format guidance
- [x] T059 [US3] Add conversation logging for order_tracking intent

**Checkpoint**: User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Catalog Browsing (Priority: P4)

**Goal**: Enable customers to browse product collections via trigger phrases

**Independent Test**: Type "New Arrivals" and verify bot returns interactive list of 5-10 products

### Tests for User Story 4

- [x] T060 [P] [US4] Create tests/integration/test_catalog_browse.py with browse flow test
- [x] T061 [P] [US4] Create tests/unit/test_services/test_product_service.py with category listing tests

### Implementation for User Story 4

- [x] T062 [US4] Add get_products_by_category method to product_service.py
- [x] T063 [US4] Implement browse trigger phrase detection ("New Arrivals", "Trending", "Sale")
- [x] T064 [US4] Implement WhatsApp interactive list message in message_builder.py
- [x] T065 [US4] Add interactive reply handling in webhook.py for product selection
- [x] T066 [US4] Implement product detail formatting when user taps list item
- [x] T067 [US4] Add empty category handling with alternative suggestions
- [x] T068 [US4] Add conversation logging for catalog_browse intent

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: n8n Integration & Human Escalation

**Purpose**: Integration with external systems for order sync and human handoff

- [x] T069 Create app/models/catalog.py with CatalogSyncPayload, CatalogSyncResponse models
- [x] T070 Implement app/api/admin.py with POST /admin/sync-catalog endpoint (API key auth)
- [x] T071 Add product upsert with embedding generation in product_service.py
- [x] T072 Implement app/services/escalation_service.py with n8n webhook notification
- [x] T073 Add confidence threshold check (70%) and escalation trigger in ai_service.py
- [x] T074 [P] Create tests/integration/test_admin_sync.py with catalog sync flow test
- [x] T075 [P] Create tests/unit/test_services/test_escalation_service.py with escalation tests

---

## Phase 8: Deployment & Polish

**Purpose**: Production readiness, deployment configuration, and documentation

- [x] T076 [P] Create Dockerfile for local development
- [x] T077 [P] Create docker-compose.yml with Redis service
- [x] T078 Create vercel.json with serverless function configuration
- [x] T079 [P] Create .github/workflows/ci.yml with GitHub Actions (lint, type check, test)
- [x] T080 Add webhook signature verification in app/api/webhook.py
- [x] T081 Add rate limiting middleware in app/main.py
- [x] T082 Run type checking with mypy and fix any issues
- [x] T083 Run security audit on dependencies
- [x] T084 Create README.md with project overview and setup instructions
- [x] T085 Update CLAUDE.md with build/test/lint commands
- [x] T086 Run quickstart.md validation to ensure all steps work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **n8n Integration (Phase 7)**: Can start after Phase 2, but benefits from US3 for order context
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - May reuse product_service from US1/US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create tests/integration/test_visual_search.py" (T027)
Task: "Create tests/unit/test_services/test_vision_service.py" (T028)
Task: "Create tests/contract/test_openai_api.py" (T029)

# Then implement models and services:
Task: "Create app/models/vision.py" (T031)
Task: "Implement app/services/vision_service.py" (T030)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 - Visual Product Search
4. **STOP and VALIDATE**: Test visual search independently
5. Deploy/demo if ready - this is your MVP!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Q&A support)
4. Add User Story 3 → Test independently → Deploy/Demo (Order tracking)
5. Add User Story 4 → Test independently → Deploy/Demo (Full catalog browsing)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Visual Search)
   - Developer B: User Story 2 (Q&A RAG)
   - Developer C: User Story 3 + 4 (Order Tracking + Browsing)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
