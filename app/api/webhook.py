"""WhatsApp webhook endpoints."""

import hashlib
import hmac
import time
from typing import Any

from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.core.logging import logger
from app.models.whatsapp import WhatsAppWebhookPayload
from app.services.whatsapp_service import whatsapp_service
from app.services.vision_service import vision_service
from app.services.product_service import product_service
from app.services.conversation_service import conversation_service
from app.services.ai_service import ai_service
from app.services.order_service import order_service
from app.utils.message_builder import (
    build_text_message,
    format_product_list_for_message,
    build_fallback_menu,
    build_catalog_list,
)
from app.utils.language import detect_language

router = APIRouter()


async def verify_webhook_signature(request: Request) -> bool:
    """
    Verify WhatsApp webhook signature.

    Meta signs webhook payloads with HMAC-SHA256 using the app secret.
    """
    if not settings.whatsapp_app_secret:
        # Skip verification if no secret configured (dev mode)
        return True

    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature:
        logger.warning("Missing X-Hub-Signature-256 header")
        return False

    # Get request body
    body = await request.body()

    # Calculate expected signature
    expected_signature = hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    # Compare signatures
    provided_signature = signature.replace("sha256=", "")
    if not hmac.compare_digest(provided_signature, expected_signature):
        logger.warning("Invalid webhook signature")
        return False

    return True


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
) -> PlainTextResponse:
    """
    Verify WhatsApp webhook subscription.

    Meta sends a GET request to verify the webhook URL.
    We must return the challenge if the verify token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook verification successful")
        return PlainTextResponse(content=hub_challenge)

    logger.warning(f"Webhook verification failed: mode={hub_mode}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    payload: WhatsAppWebhookPayload,
) -> dict[str, str]:
    """
    Handle incoming WhatsApp webhook events.

    Processes text, image, and interactive messages.
    """
    # Verify webhook signature
    if not await verify_webhook_signature(request):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Log the incoming webhook
    logger.info(f"Received webhook: {payload.object}")

    # Process each entry
    for entry in payload.entry:
        for change in entry.changes:
            if change.field != "messages":
                continue

            for message in change.value.messages:
                customer_phone = message.from_number
                message_type = message.type

                logger.info(
                    f"Processing {message_type} message from {customer_phone}"
                )

                try:
                    if message_type == "text" and message.text:
                        text_content = message.text.body
                        logger.info(f"Text message: {text_content[:100]}")
                        await handle_text_message(customer_phone, text_content)

                    elif message_type == "image" and message.image:
                        await handle_image_message(
                            customer_phone,
                            message.image.id,
                        )

                    elif message_type == "interactive" and message.interactive:
                        logger.info(f"Interactive message: {message.interactive.type}")
                        await handle_interactive_message(
                            customer_phone,
                            message.interactive,
                        )

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Send fallback menu on error
                    await whatsapp_service.send_message(
                        build_fallback_menu(customer_phone)
                    )

    return {"status": "ok"}


async def handle_text_message(customer_phone: str, text_content: str) -> None:
    """
    Handle incoming text message for Q&A support, order tracking, or catalog browse.

    Detects order IDs, browse triggers, then routes to AI service.
    """
    start_time = time.time()

    try:
        # Check for order ID in message
        order_id = order_service.extract_order_id(text_content)

        if order_id:
            # Handle as order tracking request
            await handle_order_tracking(customer_phone, order_id, start_time)
            return

        # Check for browse trigger
        browse_trigger = product_service.detect_browse_trigger(text_content)

        if browse_trigger:
            # Handle as catalog browse request
            await handle_catalog_browse(customer_phone, browse_trigger, start_time)
            return

        # Detect language from message
        language = detect_language(text_content)
        logger.info(f"Detected language: {language}")

        # Process with AI service (includes RAG and session context)
        response = await ai_service.process_text_message(
            customer_phone=customer_phone,
            message=text_content,
            language=language,
        )

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log the interaction
        await conversation_service.log_message(
            customer_phone=customer_phone,
            message_type="text",
            direction="inbound",
            content=text_content,
            intent="qa",
            response_time_ms=response_time_ms,
            metadata={"language": language},
        )

        # Send response
        await whatsapp_service.send_text(customer_phone, response)

    except Exception as e:
        logger.error(f"Text message handling failed: {e}")
        # Graceful degradation - send fallback menu
        await whatsapp_service.send_message(build_fallback_menu(customer_phone))


async def handle_order_tracking(
    customer_phone: str,
    order_id: str,
    start_time: float,
) -> None:
    """
    Handle order tracking request.

    Looks up order and sends status back to customer.
    """
    try:
        logger.info(f"Looking up order: {order_id}")

        # Get order from database
        order = await order_service.get_order_by_id(order_id)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        if order:
            # Format and send order status
            response = order_service.format_order_status(order)
            await whatsapp_service.send_text(customer_phone, response)

            # Log successful tracking
            await conversation_service.log_message(
                customer_phone=customer_phone,
                message_type="text",
                direction="inbound",
                content=order_id,
                intent="order_tracking",
                response_time_ms=response_time_ms,
                metadata={"order_id": order_id, "order_status": order.get("status")},
            )
        else:
            # Order not found
            response = order_service.format_order_not_found(order_id)
            await whatsapp_service.send_text(customer_phone, response)

            # Log failed tracking
            await conversation_service.log_message(
                customer_phone=customer_phone,
                message_type="text",
                direction="inbound",
                content=order_id,
                intent="order_tracking",
                response_time_ms=response_time_ms,
                metadata={"order_id": order_id, "found": False},
            )

    except Exception as e:
        logger.error(f"Order tracking failed: {e}")
        await whatsapp_service.send_message(build_fallback_menu(customer_phone))


async def handle_catalog_browse(
    customer_phone: str,
    trigger: str,
    start_time: float,
) -> None:
    """
    Handle catalog browsing request.

    Gets products by category and sends interactive list.
    """
    try:
        logger.info(f"Browsing catalog: {trigger}")

        # Get products based on trigger
        if trigger == "new_arrivals":
            products = await product_service.get_new_arrivals(limit=10)
        elif trigger == "trending":
            products = await product_service.get_trending(limit=10)
        elif trigger == "sale":
            products = await product_service.get_sale_items(limit=10)
        else:
            products = []

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        if products:
            # Send interactive list
            message = build_catalog_list(customer_phone, products, trigger)
            await whatsapp_service.send_message(message)

            # Log successful browse
            await conversation_service.log_message(
                customer_phone=customer_phone,
                message_type="text",
                direction="inbound",
                content=trigger,
                intent="catalog_browse",
                response_time_ms=response_time_ms,
                metadata={"category": trigger, "products_shown": len(products)},
            )
        else:
            # No products found
            response = product_service.format_empty_category(trigger)
            await whatsapp_service.send_text(customer_phone, response)

            # Log empty result
            await conversation_service.log_message(
                customer_phone=customer_phone,
                message_type="text",
                direction="inbound",
                content=trigger,
                intent="catalog_browse",
                response_time_ms=response_time_ms,
                metadata={"category": trigger, "products_shown": 0},
            )

    except Exception as e:
        logger.error(f"Catalog browse failed: {e}")
        await whatsapp_service.send_message(build_fallback_menu(customer_phone))


async def handle_interactive_message(
    customer_phone: str,
    interactive: Any,
) -> None:
    """
    Handle interactive message reply (list or button selection).

    Shows product details when user selects from list.
    """
    start_time = time.time()

    try:
        interactive_type = interactive.type

        if interactive_type == "list_reply":
            # User selected from product list
            product_id = interactive.list_reply.id
            logger.info(f"List reply selected: {product_id}")

            # Get product details
            product = await product_service.get_by_id(product_id)

            if product:
                # Format and send product details
                response = product_service.format_product_detail(product)
                await whatsapp_service.send_text(customer_phone, response)

                # Log interaction
                response_time_ms = int((time.time() - start_time) * 1000)
                await conversation_service.log_message(
                    customer_phone=customer_phone,
                    message_type="interactive",
                    direction="inbound",
                    content=product_id,
                    intent="product_detail",
                    response_time_ms=response_time_ms,
                    metadata={"product_id": product_id},
                )
            else:
                await whatsapp_service.send_text(
                    customer_phone,
                    "Sorry, I couldn't find that product. Please try again.",
                )

        elif interactive_type == "button_reply":
            # User clicked a button
            button_id = interactive.button_reply.id
            logger.info(f"Button reply: {button_id}")

            if button_id == "browse":
                await handle_catalog_browse(customer_phone, "new_arrivals", start_time)
            elif button_id == "track":
                await whatsapp_service.send_text(
                    customer_phone,
                    "Please enter your order ID (e.g., ORD-2024-001234) to track your order.",
                )
            elif button_id == "help":
                await whatsapp_service.send_text(
                    customer_phone,
                    "📞 *Need help?*\n\n"
                    "• Send a photo to find similar items\n"
                    "• Type 'New Arrivals' to browse products\n"
                    "• Enter your order ID to track shipping\n"
                    "• Ask any question about our products!",
                )

    except Exception as e:
        logger.error(f"Interactive message handling failed: {e}")
        await whatsapp_service.send_message(build_fallback_menu(customer_phone))


async def handle_image_message(customer_phone: str, media_id: str) -> None:
    """
    Handle incoming image message for visual search.

    Downloads image, analyzes with Gemini, searches products,
    and sends results back to customer.
    """
    start_time = time.time()

    try:
        # Download image from WhatsApp
        logger.info(f"Downloading media: {media_id}")
        image_bytes = await whatsapp_service.download_media(media_id)

        # Analyze image with Gemini Vision
        logger.info("Analyzing image with vision service")
        attributes = await vision_service.analyze_clothing_image(image_bytes)

        # Check if it's a valid clothing image
        if not vision_service.is_valid_clothing_result(attributes):
            reason = attributes.get("reason", "This doesn't appear to be a clothing item")
            await whatsapp_service.send_text(
                customer_phone,
                f"I can only help with clothing items. {reason}\n\n"
                "Please send a clear photo of a dress, shirt, or other clothing item you'd like to find.",
            )
            return

        # Search for similar products
        logger.info(f"Searching products with attributes: {attributes}")
        products = await product_service.search_by_attributes(attributes, limit=5)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log the interaction
        await conversation_service.log_visual_search(
            customer_phone=customer_phone,
            attributes=attributes,
            products_found=len(products),
            response_time_ms=response_time_ms,
        )

        # Send results to customer
        if products:
            # Convert dict results to Product-like objects for formatting
            from app.models.product import Product
            from datetime import datetime

            product_objects = []
            for p in products:
                product_objects.append(Product(
                    id=p["id"],
                    name=p["name"],
                    description=p.get("description"),
                    price=float(p["price"]),
                    currency=p.get("currency", "USD"),
                    supplier_url=p.get("supplier_url"),
                    image_urls=p["image_urls"],
                    sizes=p["sizes"],
                    colors=p["colors"],
                    inventory_count=p.get("inventory_count", 0),
                    category=p.get("category"),
                    tags=p.get("tags", []),
                    is_active=p.get("is_active", True),
                    created_at=datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")) if isinstance(p.get("created_at"), str) else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(p["updated_at"].replace("Z", "+00:00")) if isinstance(p.get("updated_at"), str) else datetime.utcnow(),
                ))

            response_text = format_product_list_for_message(product_objects)
            await whatsapp_service.send_text(customer_phone, response_text)
        else:
            await whatsapp_service.send_text(
                customer_phone,
                "I couldn't find any matching items in our catalog right now.\n\n"
                "Try sending another photo, or type 'New Arrivals' to browse our latest products!",
            )

    except Exception as e:
        logger.error(f"Visual search failed: {e}")
        # Graceful degradation - send fallback menu
        await whatsapp_service.send_message(build_fallback_menu(customer_phone))
