
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.sessions import SessionLocal
from app.repositories.product_repository import (
    get_product_by_product_id,
    list_products,
)
from app.schemas.product import ProductListResponse, ProductResponse

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


def get_db():
    with SessionLocal() as session:
        yield session


@router.get("", response_model=ProductListResponse)
def get_products(
    category: str | None = Query(default=None, min_length=1, max_length=80),
    max_price: Decimal | None = Query(default=None, gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
):
    items, total = list_products(
        session,
        category=category,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    session: Session = Depends(get_db),
):
    product = get_product_by_product_id(session, product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
