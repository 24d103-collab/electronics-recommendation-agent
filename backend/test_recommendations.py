
from decimal import Decimal

from app.db.sessions import SessionLocal
from app.repositories.product_repository import list_products
from app.services.recommendation_service import recommend_products


def main():
    session = SessionLocal()

    try:
        products, total = list_products(
            session,
            category="laptop",
            limit=100,
            offset=0,
        )

        print(f"Products found in catalogue: {total}")

        requirements = {
            "category": "laptop",
            "max_budget": "70000",
            "intended_uses": ["programming", "college"],
        }

        recommendations = recommend_products(session, requirements)

        print("\nRecommendations:")
        for product in recommendations:
            print(f"- {product['name']}: ₹{product['price']:,.0f}")
            print(f"  Score: {product['score']}")
            print(f"  Matched uses: {product['matched_uses']}")
            print(f"  Explanation: {product['explanation']}")

            # Verify the hard budget constraint.
            assert Decimal(str(product["price"])) <= Decimal("70000")

        assert len(recommendations) <= 2
        print("\nPASS: No recommendation exceeds the budget.")

    finally:
        session.close()


if __name__ == "__main__":
    main()
