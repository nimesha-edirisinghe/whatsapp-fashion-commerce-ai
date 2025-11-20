"""Admin API endpoints for catalog management."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Header

from app.config import settings
from app.core.logging import logger
from app.models.catalog import CatalogSyncPayload, CatalogSyncResponse
from app.services.product_service import product_service

router = APIRouter()


def verify_api_key(x_api_key: str = Header(...)) -> None:
    """Verify admin API key."""
    if x_api_key != settings.admin_api_key:
        logger.warning("Invalid admin API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("/admin/sync-catalog", response_model=CatalogSyncResponse)
async def sync_catalog(
    payload: CatalogSyncPayload,
    x_api_key: str = Header(...),
) -> CatalogSyncResponse:
    """
    Sync product catalog from external source (n8n).

    Requires API key authentication.
    Supports upsert, replace, and append modes.
    """
    # Verify API key
    verify_api_key(x_api_key)

    logger.info(
        f"Catalog sync started: {len(payload.products)} products, "
        f"mode={payload.sync_mode}, source={payload.source}"
    )

    sync_id = str(uuid.uuid4())
    created = 0
    updated = 0
    failed = 0
    errors: list[str] = []

    try:
        for product in payload.products:
            try:
                result = await product_service.upsert_product(product.model_dump())
                if result.get("created"):
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                failed += 1
                error_msg = f"Product {product.id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to sync product: {error_msg}")

        success = failed == 0
        message = (
            f"Sync completed: {created} created, {updated} updated"
            if success
            else f"Sync completed with errors: {failed} failed"
        )

        logger.info(
            f"Catalog sync completed: sync_id={sync_id}, "
            f"created={created}, updated={updated}, failed={failed}"
        )

        return CatalogSyncResponse(
            success=success,
            message=message,
            products_processed=len(payload.products),
            products_created=created,
            products_updated=updated,
            products_failed=failed,
            errors=errors[:10],  # Limit errors in response
            sync_id=sync_id,
            completed_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Catalog sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/admin/catalog/stats")
async def get_catalog_stats(
    x_api_key: str = Header(...),
) -> dict[str, Any]:
    """Get catalog statistics."""
    verify_api_key(x_api_key)

    try:
        stats = await product_service.get_catalog_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get catalog stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
