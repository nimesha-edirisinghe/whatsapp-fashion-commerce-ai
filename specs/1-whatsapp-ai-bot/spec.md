# Feature Specification: FashionImport AI Bot

**Feature Branch**: `1-whatsapp-ai-bot`
**Created**: 2025-11-20
**Status**: Draft
**Input**: WhatsApp-based automated sales and support agent for clothing import business

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Product Search (Priority: P1)

A customer uploads a photo of clothing they like (from Instagram, Pinterest, or their own wardrobe) to find similar items in the catalog. The system analyzes the image to identify style attributes (color, pattern, garment type) and returns matching products from inventory.

**Why this priority**: Visual search is the primary differentiator for this bot. It enables customers to find products without knowing exact terminology, reducing friction and increasing conversion rates.

**Independent Test**: Can be fully tested by sending an image and verifying the bot returns relevant product matches with images and prices. Delivers immediate product discovery value.

**Acceptance Scenarios**:

1. **Given** a customer sends a dress image, **When** the image is processed, **Then** the bot returns 3-5 similar dresses from inventory with images, names, and prices within 10 seconds
2. **Given** a customer sends a non-clothing image (food, landscape), **When** the image is analyzed, **Then** the bot politely explains it can only help with clothing and suggests uploading a fashion photo
3. **Given** a customer sends a blurry or very small image, **When** analysis fails, **Then** the bot requests a clearer photo with tips for better results

---

### User Story 2 - Q&A Support with Context (Priority: P2)

A customer asks natural language questions about products, availability, shipping, sizing, or policies. The bot uses conversation history to understand context (e.g., "Do you have it in red?" refers to previously discussed item) and provides accurate answers based on current inventory and business rules.

**Why this priority**: Q&A handles the majority of customer interactions and directly impacts sales conversion. Contextual understanding prevents customer frustration from repeating information.

**Independent Test**: Can be tested by asking product questions and follow-ups, verifying accurate and contextual responses. Delivers customer support value independently.

**Acceptance Scenarios**:

1. **Given** a customer asks "Do you have this in size M?", **When** there is a previous product discussed, **Then** the bot checks that specific product's inventory and responds with availability and price
2. **Given** a customer asks "How long is shipping?", **When** there is no specific product context, **Then** the bot provides general shipping timeframe (7-14 business days for standard)
3. **Given** a customer asks about something unrelated to clothing/commerce (e.g., "What's the capital of France?"), **When** the query is processed, **Then** the bot politely redirects to clothing-related assistance

---

### User Story 3 - Order Tracking (Priority: P3)

A customer provides their order ID to check shipping status. The bot retrieves the current status from the order management system and returns tracking information including estimated delivery date.

**Why this priority**: Reduces support burden for order inquiries but depends on having orders to track. Essential for post-purchase customer experience.

**Independent Test**: Can be tested by providing an order ID and verifying correct status retrieval. Delivers tracking value without other features.

**Acceptance Scenarios**:

1. **Given** a customer sends a valid order ID, **When** the order is found, **Then** the bot returns current status (Processing/Shipped/Delivered), tracking number if available, and estimated delivery date
2. **Given** a customer sends an invalid order ID, **When** lookup fails, **Then** the bot asks them to verify the ID and provides format guidance (e.g., "Order IDs look like: ORD-12345")
3. **Given** a customer asks about an order but doesn't provide ID, **When** no ID is detected, **Then** the bot asks for their order ID and explains where to find it (confirmation email)

---

### User Story 4 - Catalog Browsing (Priority: P4)

A customer types trigger phrases like "New Arrivals", "Trending", or "Sale Items" to browse curated product collections. The bot responds with an interactive list or carousel of products they can tap to learn more.

**Why this priority**: Enables product discovery for customers who don't have a specific image or question. Good for engagement but less critical than direct search/support.

**Independent Test**: Can be tested by typing "New Arrivals" and verifying interactive product list is returned. Delivers browsing value independently.

**Acceptance Scenarios**:

1. **Given** a customer types "New Arrivals", **When** the message is processed, **Then** the bot returns an interactive list of 5-10 newest products with images and prices
2. **Given** a customer taps on a product in the list, **When** they select it, **Then** the bot provides full product details (description, sizes, colors, price) with option to ask questions
3. **Given** no products match the category, **When** a browse request is made, **Then** the bot explains the category is empty and suggests alternatives

---

### Edge Cases

- What happens when the AI confidence is below 70%? System escalates to human agent via notification
- How does system handle WhatsApp 24-hour messaging window expiration? Messages outside window use pre-approved templates
- What happens when external services (AI, database) are unavailable? Retry once with 3-second timeout, then fallback to rule-based menu with pre-defined responses
- How does system handle multiple images sent in quick succession? Process only the most recent image, acknowledge receipt of others
- What happens when customer sends voice messages? Politely request text or image input instead
- How does system handle concurrent conversations from same customer? Use session management to maintain single conversation state

## Requirements *(mandatory)*

### Functional Requirements

**Webhook & Messaging**
- **FR-001**: System MUST verify WhatsApp webhook verification requests using the configured verify token
- **FR-002**: System MUST receive and process incoming text messages within 5 seconds of receipt
- **FR-003**: System MUST receive and process incoming image messages by downloading media from WhatsApp servers
- **FR-004**: System MUST respond within the 24-hour messaging window using session messages
- **FR-005**: System MUST use pre-approved message templates for communications outside 24-hour window

**Visual Search Pipeline**
- **FR-006**: System MUST analyze uploaded images to extract clothing attributes (garment type, color, pattern, style)
- **FR-007**: System MUST search product catalog using extracted image attributes to find similar items
- **FR-008**: System MUST return product matches with images, names, prices, and availability
- **FR-009**: System MUST reject non-clothing images with a polite, helpful message

**Q&A & RAG Pipeline**
- **FR-010**: System MUST convert customer questions to semantic embeddings for search
- **FR-011**: System MUST search knowledge base (products, policies, FAQs) using semantic similarity
- **FR-012**: System MUST generate responses using retrieved context and customer's conversation history
- **FR-013**: System MUST maintain last 10 messages per customer for conversation context
- **FR-023**: System MUST auto-detect customer's language from their message and respond in the same language

**Order Tracking**
- **FR-014**: System MUST retrieve order status from order management system using order ID
- **FR-015**: System MUST return order status, tracking number, and estimated delivery date

**Catalog Browsing**
- **FR-016**: System MUST recognize browse trigger phrases ("New Arrivals", "Trending", "Sale")
- **FR-017**: System MUST return interactive product lists/carousels with tappable items

**Session & Context**
- **FR-018**: System MUST persist conversation context per customer for contextual responses
- **FR-019**: System MUST expire session data after 24 hours of inactivity

**Human Escalation**
- **FR-020**: System MUST escalate to human agent when AI confidence is below 70%
- **FR-021**: System MUST notify support team of escalation with conversation context

**Content Filtering**
- **FR-022**: System MUST politely decline non-clothing-related queries and redirect to relevant assistance

### Key Entities

- **Customer**: WhatsApp user identified by phone number; has conversation history and active session
- **Product**: Catalog item with name, description, images, price, sizes (universal format: S/M/L/XL and/or numeric), colors, inventory count, and embedding vector
- **Conversation**: Session containing message history, current context, and product references
- **Order**: Customer purchase with order ID, status, tracking info, items, and delivery estimate
- **Message**: Individual communication with type (text/image), content, timestamp, and direction (inbound/outbound)

### Assumptions

- Customers have active WhatsApp accounts and internet connectivity
- Product catalog is pre-populated with images and metadata
- Shipping timeframe is 7-14 business days for standard delivery
- Order management system is accessible via n8n automation
- Business operates in a single timezone for order processing
- Maximum 5 products returned per visual search to avoid message clutter
- Interactive lists limited to 10 items per WhatsApp API constraints

## Clarifications

### Session 2025-11-20

- Q: How should the bot determine response language? → A: Auto-detect from message language
- Q: What sizing standard should products use? → A: Universal/Numeric (S/M/L/XL + numeric where applicable)
- Q: What retry strategy for external service failures? → A: Retry once with 3-second timeout, then fallback

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Visual search returns relevant product matches within 10 seconds for 95% of clothing images
- **SC-002**: Q&A responses are contextually accurate for 85% of follow-up questions
- **SC-003**: Order tracking provides correct status information for 99% of valid order IDs
- **SC-004**: System handles 100 concurrent customer conversations without degradation
- **SC-005**: Customer queries are resolved without human intervention for 80% of conversations
- **SC-006**: Human escalation occurs within 30 seconds when confidence threshold is not met
- **SC-007**: System maintains 99.5% uptime during business hours
- **SC-008**: Non-clothing image filtering correctly identifies and rejects 90% of irrelevant images
