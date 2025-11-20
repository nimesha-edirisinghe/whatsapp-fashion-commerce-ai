"""Order service for order tracking operations."""

import re
from typing import Any

from app.core.database import supabase
from app.core.logging import logger


class OrderService:
    """Service for order tracking operations."""

    # Order ID pattern: ORD-YYYY-NNNNNN
    ORDER_ID_PATTERN = re.compile(r"ORD-\d{4}-\d{6}", re.IGNORECASE)

    async def get_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        """
        Get order by ID.

        Args:
            order_id: Order ID (e.g., ORD-2024-001234)

        Returns:
            Order data or None if not found
        """
        try:
            result = (
                supabase.table("orders")
                .select("*")
                .eq("id", order_id.upper())
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Get order by ID failed: {e}")
            return None

    async def get_orders_by_phone(
        self,
        customer_phone: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Get recent orders for a customer.

        Args:
            customer_phone: Customer phone number
            limit: Maximum orders to return

        Returns:
            List of orders
        """
        try:
            result = (
                supabase.table("orders")
                .select("*")
                .eq("customer_phone", customer_phone)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Get orders by phone failed: {e}")
            return []

    def is_valid_order_id(self, order_id: str) -> bool:
        """
        Check if string is a valid order ID format.

        Args:
            order_id: String to check

        Returns:
            True if valid format
        """
        if not order_id:
            return False
        return bool(self.ORDER_ID_PATTERN.fullmatch(order_id))

    def extract_order_id(self, message: str) -> str | None:
        """
        Extract order ID from message text.

        Args:
            message: User message

        Returns:
            Extracted order ID (uppercase) or None
        """
        match = self.ORDER_ID_PATTERN.search(message)
        if match:
            return match.group().upper()
        return None

    def format_order_status(self, order: dict[str, Any]) -> str:
        """
        Format order status for WhatsApp message.

        Args:
            order: Order data

        Returns:
            Formatted status message
        """
        order_id = order.get("id", "Unknown")
        status = order.get("status", "unknown")

        # Status emoji mapping
        status_emoji = {
            "pending": "⏳",
            "processing": "📦",
            "shipped": "🚚",
            "delivered": "✅",
            "cancelled": "❌",
        }
        emoji = status_emoji.get(status, "📋")

        lines = [
            f"{emoji} *Order Status*",
            f"Order: {order_id}",
            f"Status: {status.title()}",
        ]

        # Add tracking info if shipped
        if status == "shipped":
            if tracking := order.get("tracking_number"):
                lines.append(f"Tracking: {tracking}")
            if carrier := order.get("carrier"):
                lines.append(f"Carrier: {carrier}")
            if eta := order.get("estimated_delivery"):
                lines.append(f"Est. Delivery: {eta}")

        # Add delivery info if delivered
        if status == "delivered":
            if delivered_at := order.get("delivered_at"):
                lines.append(f"Delivered: {delivered_at}")

        # Add items summary
        items = order.get("items", [])
        if items:
            lines.append("")
            lines.append("*Items:*")
            for item in items:
                name = item.get("name", "Item")
                qty = item.get("quantity", 1)
                lines.append(f"• {name} x{qty}")

        # Add total if available
        if total := order.get("total_amount"):
            currency = order.get("currency", "USD")
            lines.append(f"\nTotal: {currency} {total:.2f}")

        return "\n".join(lines)

    def format_order_not_found(self, order_id: str) -> str:
        """
        Format message for order not found.

        Args:
            order_id: The order ID that wasn't found

        Returns:
            Formatted message
        """
        return (
            f"❓ I couldn't find order *{order_id}* in our system.\n\n"
            "Please check the order ID and try again. "
            "You can find your order ID in your confirmation email.\n\n"
            "If you need help, type 'Help' to see options."
        )

    def format_invalid_order_id(self) -> str:
        """
        Format message for invalid order ID format.

        Returns:
            Formatted message with format guidance
        """
        return (
            "📝 Order IDs follow this format: *ORD-YYYY-NNNNNN*\n\n"
            "Example: ORD-2024-001234\n\n"
            "You can find your order ID in your confirmation email. "
            "Please enter the complete order ID to track your order."
        )


# Singleton instance
order_service = OrderService()
