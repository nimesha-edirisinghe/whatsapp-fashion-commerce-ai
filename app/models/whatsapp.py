"""WhatsApp API request/response models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


# Incoming webhook models
class WhatsAppTextContent(BaseModel):
    """Text message content."""
    body: str


class WhatsAppImageContent(BaseModel):
    """Image message content."""
    id: str
    mime_type: str = Field(alias="mime_type")


class WhatsAppInteractiveReply(BaseModel):
    """Interactive message reply."""
    id: str
    title: str


class WhatsAppInteractiveContent(BaseModel):
    """Interactive message content."""
    type: str
    list_reply: WhatsAppInteractiveReply | None = None
    button_reply: WhatsAppInteractiveReply | None = None


class WhatsAppMessage(BaseModel):
    """Incoming WhatsApp message."""
    id: str = Field(alias="id")
    from_number: str = Field(alias="from")
    timestamp: str
    type: Literal["text", "image", "interactive", "button"]
    text: WhatsAppTextContent | None = None
    image: WhatsAppImageContent | None = None
    interactive: WhatsAppInteractiveContent | None = None

    class Config:
        populate_by_name = True


class WhatsAppMetadata(BaseModel):
    """Webhook metadata."""
    display_phone_number: str
    phone_number_id: str


class WhatsAppValue(BaseModel):
    """Webhook value payload."""
    messaging_product: str
    metadata: WhatsAppMetadata
    messages: list[WhatsAppMessage] = []


class WhatsAppChange(BaseModel):
    """Webhook change entry."""
    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    """Webhook entry."""
    id: str
    changes: list[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    """Complete webhook payload from WhatsApp."""
    object: str
    entry: list[WhatsAppEntry]


# Outgoing message models
class OutgoingTextMessage(BaseModel):
    """Outgoing text message."""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "text"
    text: dict[str, str]


class OutgoingImageMessage(BaseModel):
    """Outgoing image message."""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "image"
    image: dict[str, str]


class ListRow(BaseModel):
    """Row in interactive list."""
    id: str
    title: str
    description: str = ""


class ListSection(BaseModel):
    """Section in interactive list."""
    title: str
    rows: list[ListRow]


class InteractiveListAction(BaseModel):
    """Action for interactive list."""
    button: str
    sections: list[ListSection]


class InteractiveBody(BaseModel):
    """Body for interactive message."""
    text: str


class InteractiveHeader(BaseModel):
    """Header for interactive message."""
    type: str = "text"
    text: str


class OutgoingInteractiveList(BaseModel):
    """Outgoing interactive list message."""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "interactive"
    interactive: dict[str, Any]
