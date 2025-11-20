"""WhatsApp message formatting helpers."""

from typing import Any

from app.models.product import Product


def build_text_message(to: str, text: str) -> dict[str, Any]:
    """Build a text message payload."""
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }


def build_image_message(to: str, image_url: str, caption: str = "") -> dict[str, Any]:
    """Build an image message payload."""
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "image",
        "image": {"link": image_url},
    }
    if caption:
        payload["image"]["caption"] = caption
    return payload


def build_interactive_list(
    to: str,
    body_text: str,
    button_text: str,
    sections: list[dict[str, Any]],
    header_text: str = "",
) -> dict[str, Any]:
    """Build an interactive list message payload."""
    interactive: dict[str, Any] = {
        "type": "list",
        "body": {"text": body_text},
        "action": {
            "button": button_text,
            "sections": sections,
        },
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": header_text}

    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    }


def build_interactive_buttons(
    to: str,
    body_text: str,
    buttons: list[dict[str, str]],
    header_text: str = "",
) -> dict[str, Any]:
    """Build an interactive buttons message payload."""
    interactive: dict[str, Any] = {
        "type": "button",
        "body": {"text": body_text},
        "action": {
            "buttons": [
                {"type": "reply", "reply": btn} for btn in buttons
            ],
        },
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": header_text}

    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    }


def format_product_result(product: Product) -> str:
    """Format a single product for text display."""
    sizes = ", ".join(product.sizes)
    colors = ", ".join(product.colors)
    return (
        f"*{product.name}*\n"
        f"💰 ${product.price:.2f}\n"
        f"📏 Sizes: {sizes}\n"
        f"🎨 Colors: {colors}\n"
        f"📦 In stock: {product.inventory_count}"
    )


def format_product_list_for_message(products: list[Product]) -> str:
    """Format multiple products for text message."""
    if not products:
        return "No products found matching your search."

    lines = ["Here are some items you might like:\n"]
    for i, product in enumerate(products[:5], 1):
        lines.append(f"{i}. {format_product_result(product)}\n")

    return "\n".join(lines)


def build_product_list_sections(products: list[Product]) -> list[dict[str, Any]]:
    """Build sections for interactive list from products."""
    rows = []
    for product in products[:10]:  # WhatsApp limit
        rows.append({
            "id": product.id,
            "title": product.name[:24],  # WhatsApp limit
            "description": f"${product.price:.2f} - {', '.join(product.sizes[:3])}",
        })

    return [{"title": "Products", "rows": rows}]


def format_order_status(
    order_id: str,
    status: str,
    tracking_number: str | None = None,
    estimated_delivery: str | None = None,
) -> str:
    """Format order status for display."""
    lines = [
        f"📦 *Order Status*",
        f"Order ID: {order_id}",
        f"Status: {status}",
    ]
    if tracking_number:
        lines.append(f"Tracking: {tracking_number}")
    if estimated_delivery:
        lines.append(f"Est. Delivery: {estimated_delivery}")

    return "\n".join(lines)


def build_fallback_menu(to: str) -> dict[str, Any]:
    """Build fallback menu when AI fails."""
    return build_interactive_buttons(
        to=to,
        body_text=(
            "I'm having trouble understanding. "
            "Please choose an option or try rephrasing your question."
        ),
        buttons=[
            {"id": "browse", "title": "Browse Products"},
            {"id": "track", "title": "Track Order"},
            {"id": "help", "title": "Get Help"},
        ],
        header_text="How can I help?",
    )


def build_catalog_list(
    to: str,
    products: list[dict[str, Any]],
    category: str,
) -> dict[str, Any]:
    """
    Build interactive list for catalog browsing.

    Args:
        to: Recipient phone number
        products: List of product dicts
        category: Category name for header

    Returns:
        WhatsApp interactive list message payload
    """
    # Format products for list rows
    rows = []
    for product in products[:10]:  # WhatsApp limit
        price = product.get("price", 0)
        currency = product.get("currency", "USD")
        rows.append({
            "id": product.get("id", ""),
            "title": product.get("name", "Product")[:24],  # WhatsApp limit
            "description": f"{currency} {price:.2f}"[:72],  # WhatsApp limit
        })

    # Build category display name
    category_display = category.replace("_", " ").title()

    return build_interactive_list(
        to=to,
        header_text=f"🛍️ {category_display}",
        body_text=f"Found {len(products)} items. Tap to see details:",
        button_text="View Products",
        sections=[{"title": category_display, "rows": rows}],
    )
