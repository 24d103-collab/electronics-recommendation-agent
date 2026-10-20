
from sqlalchemy import func

from app.db.models import Product
from app.db.sessions import SessionLocal


def main():
    with SessionLocal() as session:
        rows = (
            session.query(Product.category, func.count(Product.id))
            .group_by(Product.category)
            .order_by(Product.category)
            .all()
        )

        total = sum(count for _, count in rows)

        print("Product counts by category:")
        for category, count in rows:
            print(f"  {category}: {count}")

        print(f"\nTotal products: {total}")
        print(f"Total categories: {len(rows)}")

        assert total >= 19, f"Expected at least 19 products, found {total}"
        assert len(rows) >= 8, (
            f"Expected at least 8 categories, found {len(rows)}"
        )

        print("\nPASS: Multi-category catalogue verified.")


if __name__ == "__main__":
    main()
