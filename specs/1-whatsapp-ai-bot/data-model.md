# Data Model: FashionImport AI Bot

**Date**: 2025-11-20
**Branch**: `1-whatsapp-ai-bot`

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐
│   Product   │       │    Order    │
├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │
│ name        │       │ order_id    │
│ description │       │ customer_   │
│ price       │◄──────┤ phone (FK)  │
│ embedding   │       │ status      │
│ sizes[]     │       │ items[]     │
│ colors[]    │       │ total       │
│ inventory   │       └─────────────┘
└─────────────┘              │
       │                     │
       │                     │
       ▼                     ▼
┌─────────────────────────────────┐
│         Conversation            │
├─────────────────────────────────┤
│ id (PK)                         │
│ customer_phone                  │
│ message_type                    │
│ direction                       │
│ content                         │
│ intent                          │
│ confidence_score                │
└─────────────────────────────────┘

┌─────────────────┐
│  KnowledgeBase  │
├─────────────────┤
│ id (PK)         │
│ content_type    │
│ title           │
│ content         │
│ embedding       │
└─────────────────┘
```

## Entities

### Product

Represents a catalog item available for sale.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Product display name |
| description | TEXT | - | Detailed product description |
| price | DECIMAL(10,2) | NOT NULL | Price in default currency |
| currency | VARCHAR(3) | DEFAULT 'USD' | ISO currency code |
| supplier_url | TEXT | - | Link to Shein/Temu source |
| image_urls | TEXT[] | NOT NULL | Array of product image URLs |
| sizes | TEXT[] | NOT NULL | Available sizes (S/M/L/XL or numeric) |
| colors | TEXT[] | NOT NULL | Available colors |
| inventory_count | INTEGER | DEFAULT 0 | Current stock level |
| category | VARCHAR(100) | - | Product category (dress, shirt, etc.) |
| tags | TEXT[] | - | Search tags (casual, formal, summer) |
| embedding | vector(1536) | - | Text embedding for RAG search |
| metadata | JSONB | DEFAULT '{}' | Flexible additional data |
| is_active | BOOLEAN | DEFAULT true | Whether product is visible |
| created_at | TIMESTAMPTZ | auto | Creation timestamp |
| updated_at | TIMESTAMPTZ | auto | Last update timestamp |

**Validation Rules**:
- `price` must be > 0
- `sizes` must contain at least one size
- `colors` must contain at least one color
- `image_urls` must contain at least one URL

**State Transitions**:
- Active → Inactive (when inventory = 0 or manually disabled)
- Inactive → Active (when restocked or re-enabled)

### Order

Represents a customer purchase with tracking information.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Internal identifier |
| order_id | VARCHAR(50) | UNIQUE, NOT NULL | External order ID (ORD-12345) |
| customer_phone | VARCHAR(20) | NOT NULL | Customer WhatsApp number |
| status | VARCHAR(50) | NOT NULL | Order status |
| tracking_number | VARCHAR(100) | - | Carrier tracking number |
| carrier | VARCHAR(100) | - | Shipping carrier name |
| estimated_delivery | DATE | - | Expected delivery date |
| items | JSONB | NOT NULL | Ordered items with quantities |
| total_amount | DECIMAL(10,2) | NOT NULL | Order total |
| shipping_address | JSONB | - | Delivery address |
| metadata | JSONB | DEFAULT '{}' | Additional order data |
| created_at | TIMESTAMPTZ | auto | Order creation time |
| updated_at | TIMESTAMPTZ | auto | Last status update |

**Order Status Values**:
- `Processing` - Order received, preparing for shipment
- `Shipped` - Package dispatched, tracking available
- `In Transit` - Package with carrier
- `Delivered` - Successfully delivered
- `Cancelled` - Order cancelled

**Items JSONB Structure**:
```json
[
  {
    "product_id": "uuid",
    "name": "Summer Dress",
    "size": "M",
    "color": "Blue",
    "quantity": 1,
    "unit_price": 29.99
  }
]
```

### Conversation

Stores message history for analytics and debugging.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Message identifier |
| customer_phone | VARCHAR(20) | NOT NULL | Customer WhatsApp number |
| message_type | VARCHAR(20) | NOT NULL | text, image, interactive |
| direction | VARCHAR(10) | NOT NULL | inbound, outbound |
| content | TEXT | - | Message content or description |
| intent | VARCHAR(50) | - | Detected intent |
| confidence_score | DECIMAL(3,2) | - | AI confidence (0.00-1.00) |
| response_time_ms | INTEGER | - | Processing time in ms |
| escalated | BOOLEAN | DEFAULT false | Whether escalated to human |
| metadata | JSONB | DEFAULT '{}' | Additional context |
| created_at | TIMESTAMPTZ | auto | Message timestamp |

**Intent Values**:
- `visual_search` - Image-based product search
- `qa` - Question/answer query
- `order_tracking` - Order status inquiry
- `catalog_browse` - Category browsing request
- `greeting` - Initial greeting
- `unclear` - Could not determine intent

### KnowledgeBase

Stores policies, FAQs, and product info for RAG retrieval.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Document identifier |
| content_type | VARCHAR(50) | NOT NULL | Document type |
| title | VARCHAR(255) | NOT NULL | Document title |
| content | TEXT | NOT NULL | Full text content |
| embedding | vector(1536) | - | Text embedding for search |
| metadata | JSONB | DEFAULT '{}' | Additional metadata |
| is_active | BOOLEAN | DEFAULT true | Whether searchable |
| created_at | TIMESTAMPTZ | auto | Creation time |
| updated_at | TIMESTAMPTZ | auto | Last update |

**Content Types**:
- `policy` - Shipping, returns, privacy policies
- `faq` - Frequently asked questions
- `size_guide` - Sizing information
- `product_info` - Detailed product guides

## Session Data (Redis)

Session data stored in Redis for fast access during conversations.

### Conversation History
**Key**: `session:{phone}:messages`
**Type**: List
**TTL**: 24 hours

```json
[
  {
    "role": "user",
    "content": "Do you have summer dresses?",
    "timestamp": "2025-11-20T10:30:00Z"
  },
  {
    "role": "assistant",
    "content": "Yes! We have several summer dresses...",
    "timestamp": "2025-11-20T10:30:02Z",
    "products_mentioned": ["uuid1", "uuid2"]
  }
]
```

### Current Context
**Key**: `session:{phone}:context`
**Type**: Hash
**TTL**: 24 hours

```json
{
  "last_product_id": "uuid",
  "last_intent": "visual_search",
  "language": "en"
}
```

## Indexes

### Products
- `ivfflat` on `embedding` for vector similarity search
- B-tree on `category` for filtered queries
- B-tree on `is_active` for active product listing

### Orders
- B-tree on `order_id` for order lookup
- B-tree on `customer_phone` for customer order history

### Conversations
- B-tree on `customer_phone` for conversation history
- B-tree on `intent` for analytics
- B-tree on `created_at` for time-based queries

### KnowledgeBase
- `ivfflat` on `embedding` for RAG retrieval
- B-tree on `content_type` for filtered queries

## Pydantic Models

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Product(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price: float = Field(gt=0)
    currency: str = "USD"
    supplier_url: Optional[str]
    image_urls: list[str] = Field(min_length=1)
    sizes: list[str] = Field(min_length=1)
    colors: list[str] = Field(min_length=1)
    inventory_count: int = 0
    category: Optional[str]
    tags: list[str] = []
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class OrderItem(BaseModel):
    product_id: str
    name: str
    size: str
    color: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)

class Order(BaseModel):
    id: str
    order_id: str
    customer_phone: str
    status: str
    tracking_number: Optional[str]
    carrier: Optional[str]
    estimated_delivery: Optional[str]
    items: list[OrderItem]
    total_amount: float
    created_at: datetime
    updated_at: datetime
```
