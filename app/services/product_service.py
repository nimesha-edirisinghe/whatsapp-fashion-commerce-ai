"""Product service for catalog operations."""

from typing import Any

from app.core.database import supabase
from app.core.openai_client import create_embedding
from app.core.logging import logger
from app.core.exceptions import DatabaseError
from app.models.product import Product, ProductSearchResult
from app.utils.retry import async_retry


class ProductService:
    """Service for product catalog operations."""

    @async_retry(attempts=1, timeout=3.0)
    async def search_by_embedding(
        self,
        embedding: list[float],
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search products by vector similarity.

        Args:
            embedding: Query embedding vector
            limit: Maximum results to return
            threshold: Minimum similarity threshold

        Returns:
            List of matching products with similarity scores
        """
        try:
            result = supabase.rpc(
                "match_products",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": limit,
                },
            ).execute()

            return result.data or []
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise DatabaseError(f"Product search failed: {e}")

    async def search_by_attributes(
        self,
        attributes: dict[str, Any],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search products by clothing attributes.

        Creates embedding from attributes and performs vector search.

        Args:
            attributes: Dict with garment_type, colors, patterns, style_keywords
            limit: Maximum results to return

        Returns:
            List of matching products
        """
        # Build search query from attributes
        query_parts = []

        if garment_type := attributes.get("garment_type"):
            query_parts.append(garment_type)

        if colors := attributes.get("colors"):
            query_parts.extend(colors)

        if patterns := attributes.get("patterns"):
            query_parts.extend(patterns)

        if style_keywords := attributes.get("style_keywords"):
            query_parts.extend(style_keywords)

        if not query_parts:
            return []

        # Create embedding for the combined query
        query_text = " ".join(query_parts)
        logger.info(f"Searching products with query: {query_text}")

        try:
            embedding = await create_embedding(query_text)
            return await self.search_by_embedding(embedding, limit)
        except Exception as e:
            logger.error(f"Attribute search failed: {e}")
            # Fallback to basic category search
            return await self.search_by_category(
                attributes.get("garment_type", ""),
                limit,
            )

    async def search_by_category(
        self,
        category: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search products by category (fallback search).

        Args:
            category: Product category
            limit: Maximum results

        Returns:
            List of products in category
        """
        try:
            result = (
                supabase.table("products")
                .select("*")
                .eq("is_active", True)
                .ilike("category", f"%{category}%")
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Category search failed: {e}")
            return []

    async def get_by_id(self, product_id: str) -> dict[str, Any] | None:
        """Get product by ID."""
        try:
            result = (
                supabase.table("products")
                .select("*")
                .eq("id", product_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Get product by ID failed: {e}")
            return None

    async def get_new_arrivals(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get newest products."""
        try:
            result = (
                supabase.table("products")
                .select("*")
                .eq("is_active", True)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Get new arrivals failed: {e}")
            return []

    async def get_trending(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get trending/popular products."""
        try:
            result = (
                supabase.table("products")
                .select("*")
                .eq("is_active", True)
                .order("view_count", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Get trending failed: {e}")
            return []

    async def get_sale_items(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get products on sale."""
        try:
            result = (
                supabase.table("products")
                .select("*")
                .eq("is_active", True)
                .eq("on_sale", True)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Get sale items failed: {e}")
            return []

    def detect_browse_trigger(self, message: str) -> str | None:
        """
        Detect browse trigger phrase in message.

        Args:
            message: User message

        Returns:
            Trigger type or None
        """
        message_lower = message.lower()

        # New arrivals triggers
        if any(phrase in message_lower for phrase in ["new arrivals", "newest", "just in", "latest"]):
            return "new_arrivals"

        # Trending triggers
        if any(phrase in message_lower for phrase in ["trending", "popular", "best seller", "top rated"]):
            return "trending"

        # Sale triggers
        if any(phrase in message_lower for phrase in ["sale", "discount", "clearance", "deal"]):
            return "sale"

        return None

    def format_product_for_list(self, product: dict[str, Any]) -> dict[str, str]:
        """
        Format product for WhatsApp list item.

        Args:
            product: Product data

        Returns:
            Dict with id, title, description
        """
        price = product.get("price", 0)
        currency = product.get("currency", "USD")

        return {
            "id": product.get("id", ""),
            "title": product.get("name", "Product")[:24],  # WhatsApp limit
            "description": f"{currency} {price:.2f}"[:72],  # WhatsApp limit
        }

    def format_product_detail(self, product: dict[str, Any]) -> str:
        """
        Format product details for display.

        Args:
            product: Product data

        Returns:
            Formatted detail string
        """
        name = product.get("name", "Product")
        description = product.get("description", "")
        price = product.get("price", 0)
        currency = product.get("currency", "USD")
        sizes = product.get("sizes", [])
        colors = product.get("colors", [])

        lines = [
            f"👗 *{name}*",
            "",
        ]

        if description:
            lines.append(description)
            lines.append("")

        lines.append(f"💰 Price: {currency} {price:.2f}")

        if sizes:
            lines.append(f"📏 Sizes: {', '.join(sizes)}")

        if colors:
            lines.append(f"🎨 Colors: {', '.join(colors)}")

        lines.append("")
        lines.append("Reply with the size and color you want to order!")

        return "\n".join(lines)

    def format_empty_category(self, category: str) -> str:
        """
        Format message for empty category.

        Args:
            category: Category name

        Returns:
            Formatted message with suggestions
        """
        category_display = category.replace("_", " ").title()

        return (
            f"😅 We don't have any {category_display} products right now.\n\n"
            "Try browsing:\n"
            "• *New Arrivals* - Our latest products\n"
            "• *Trending* - Popular items\n"
            "• *Sale* - Discounted items\n\n"
            "Or send a photo of what you're looking for!"
        )

    async def upsert_product(self, product_data: dict[str, Any]) -> dict[str, Any]:
        """
        Upsert product with embedding generation.

        Args:
            product_data: Product data dict

        Returns:
            Dict with created flag and product id
        """
        try:
            product_id = product_data.get("id")

            # Generate embedding from product description
            text_for_embedding = self._build_embedding_text(product_data)
            embedding = await create_embedding(text_for_embedding)

            # Prepare data for upsert
            upsert_data = {
                **product_data,
                "embedding": embedding,
            }

            # Check if product exists
            existing = await self.get_by_id(product_id) if product_id else None

            if existing:
                # Update existing product
                result = (
                    supabase.table("products")
                    .update(upsert_data)
                    .eq("id", product_id)
                    .execute()
                )
                return {"created": False, "id": product_id}
            else:
                # Insert new product
                result = (
                    supabase.table("products")
                    .insert(upsert_data)
                    .execute()
                )
                new_id = result.data[0]["id"] if result.data else product_id
                return {"created": True, "id": new_id}

        except Exception as e:
            logger.error(f"Product upsert failed: {e}")
            raise DatabaseError(f"Failed to upsert product: {e}")

    def _build_embedding_text(self, product_data: dict[str, Any]) -> str:
        """Build text for embedding from product data."""
        parts = [
            product_data.get("name", ""),
            product_data.get("description", ""),
            product_data.get("category", ""),
        ]

        # Add colors and sizes
        if colors := product_data.get("colors"):
            parts.extend(colors)
        if tags := product_data.get("tags"):
            parts.extend(tags)

        return " ".join(filter(None, parts))

    async def get_catalog_stats(self) -> dict[str, Any]:
        """Get catalog statistics."""
        try:
            # Get total products
            total_result = (
                supabase.table("products")
                .select("id", count="exact")
                .execute()
            )

            # Get active products
            active_result = (
                supabase.table("products")
                .select("id", count="exact")
                .eq("is_active", True)
                .execute()
            )

            # Get sale products
            sale_result = (
                supabase.table("products")
                .select("id", count="exact")
                .eq("on_sale", True)
                .execute()
            )

            return {
                "total_products": total_result.count or 0,
                "active_products": active_result.count or 0,
                "sale_products": sale_result.count or 0,
            }
        except Exception as e:
            logger.error(f"Failed to get catalog stats: {e}")
            return {
                "total_products": 0,
                "active_products": 0,
                "sale_products": 0,
                "error": str(e),
            }


# Singleton instance
product_service = ProductService()
