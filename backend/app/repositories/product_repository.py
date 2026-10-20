
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Product


def list_products(
    session: Session,
    *,
    category: str | None = None,
    max_price: Decimal | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Product], int]:
    """
    Return matching products and the total number of matches.

    limit and offset control pagination.
    """
    statement = select(Product).where(Product.is_available.is_(True))

    if category:
        statement = statement.where(Product.category == category)

    if max_price is not None:
        statement = statement.where(Product.price <= max_price)

    count_statement = select(Product.id).where(
        Product.is_available.is_(True)
    )

    if category:
        count_statement = count_statement.where(
            Product.category == category
        )

    if max_price is not None:
        count_statement = count_statement.where(
            Product.price <= max_price
        )

    total = len(session.scalars(count_statement).all())

    statement = (
        statement.order_by(Product.price.asc(), Product.id.asc())
        .offset(offset)
        .limit(limit)
    )

    products = list(session.scalars(statement).all())
    return products, total


def get_product_by_product_id(
    session: Session,
    product_id: str,
) -> Product | None:
    """Retrieve one product by its public product ID."""
    statement = select(Product).where(
        Product.product_id == product_id
    )
    return session.scalar(statement)
