import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from ...core.auth import authenticate_request
from ...core.database_pool import db_pool
from ...models.auth import AuthenticatedUser


router = APIRouter()
logger = logging.getLogger(__name__)


class PropertyListItem(BaseModel):
    id: str
    name: str
    timezone: str


class PropertyListResponse(BaseModel):
    items: list[PropertyListItem]
    total: int
    page: int
    page_size: int


@router.get("/properties", response_model=PropertyListResponse)
async def list_properties(
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000),
    current_user: AuthenticatedUser = Depends(authenticate_request),
) -> PropertyListResponse:
    """List properties belonging to the authenticated user's tenant."""
    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=403, detail="No tenant assigned")

    where_clause = "tenant_id = :tenant_id"
    parameters = {"tenant_id": tenant_id}

    normalized_search = search.strip() if search else ""
    if normalized_search:
        where_clause += " AND (id ILIKE :search OR name ILIKE :search)"
        parameters["search"] = f"%{normalized_search}%"

    offset = (page - 1) * page_size

    try:
        await db_pool.initialize()
        async with db_pool.get_session() as session:
            count_result = await session.execute(
                text(f"SELECT COUNT(*) FROM properties WHERE {where_clause}"),
                parameters,
            )
            total = int(count_result.scalar_one())

            result = await session.execute(
                text(
                    f"""
                    SELECT id, name, timezone
                    FROM properties
                    WHERE {where_clause}
                    ORDER BY id, name
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {**parameters, "limit": page_size, "offset": offset},
            )

            items = [PropertyListItem(**row) for row in result.mappings().all()]
            return PropertyListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Failed to list properties for tenant %s", tenant_id
        )
        raise HTTPException(
            status_code=500, detail="Failed to load properties"
        ) from exc
