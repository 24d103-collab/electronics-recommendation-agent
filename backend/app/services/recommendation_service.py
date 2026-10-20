
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.product_repository import list_products


SPECIALIZED_USES = {
    "machine learning",
    "gaming",
    "video editing",
    "3d rendering",
}


def _normalize(value: Any) -> str:
    """Convert a value to normalized searchable text."""
    return str(value).strip().lower()


def _flatten_catalogue_value(value: Any) -> str:
    """Convert nested catalogue data into searchable text."""
    if isinstance(value, dict):
        return " ".join(
            f"{_flatten_catalogue_value(key)} "
            f"{_flatten_catalogue_value(item)}"
            for key, item in value.items()
        )

    if isinstance(value, (list, tuple, set)):
        return " ".join(
            _flatten_catalogue_value(item) for item in value
        )

    if value is None:
        return ""

    return str(value).lower()


def _get_product_uses(product: Any) -> set[str]:
    """Read intended uses safely from a product record."""
    uses = getattr(product, "intended_uses", None) or []

    if not isinstance(uses, (list, tuple, set)):
        return set()

    return {
        _normalize(use)
        for use in uses
        if _normalize(use)
    }


def _get_searchable_text(product: Any) -> str:
    """Build searchable text from actual product catalogue fields."""
    fields = [
        getattr(product, "name", ""),
        getattr(product, "description", ""),
        getattr(product, "category", ""),
        getattr(product, "specifications", {}),
        getattr(product, "features", []),
        getattr(product, "intended_uses", []),
    ]

    return " ".join(
        _flatten_catalogue_value(field) for field in fields
    )


def _preference_matches(
    preference: str,
    searchable_text: str,
) -> bool:
    """Match a preference against actual catalogue text."""
    normalized = " ".join(preference.lower().split())

    if not normalized:
        return False

    return normalized in " ".join(searchable_text.split())


def recommend_products(
    session: Session,
    requirements: dict,
    limit: int = 2,
) -> list[dict]:
    """
    Apply hard constraints, rank eligible products, and explain results.

    Category, budget, and availability are mandatory constraints.
    Intended uses and preferences influence ranking.
    """
    if not isinstance(requirements, dict):
        return []

    category = requirements.get("category")
    max_budget = requirements.get("max_budget")

    if not isinstance(category, str) or not category.strip():
        return []

    if max_budget is None or isinstance(max_budget, bool):
        return []

    try:
        budget = Decimal(str(max_budget))
    except (InvalidOperation, ValueError, TypeError):
        return []

    if not budget.is_finite() or budget <= 0:
        return []

    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        return []

    raw_uses = requirements.get("intended_uses", [])
    raw_preferences = requirements.get("preferences", [])

    intended_uses = (
        {
            _normalize(use)
            for use in raw_uses
            if isinstance(use, str) and use.strip()
        }
        if isinstance(raw_uses, list)
        else set()
    )

    preferences = (
        {
            _normalize(preference)
            for preference in raw_preferences
            if isinstance(preference, str) and preference.strip()
        }
        if isinstance(raw_preferences, list)
        else set()
    )

    category = category.strip().lower()

    # Retrieve candidates matching the requested category and budget.
    products, _ = list_products(
        session,
        category=category,
        max_price=float(budget),
        limit=100,
        offset=0,
    )

    results = []

    for product in products:
        product_category = _normalize(
            getattr(product, "category", "")
        )

        # Hard constraint: category must match exactly.
        if product_category != category:
            continue

        # Hard constraint: product must explicitly be available.
        if getattr(product, "is_available", False) is not True:
            continue

        try:
            price = Decimal(str(product.price))
        except (
            InvalidOperation,
            ValueError,
            TypeError,
            AttributeError,
        ):
            continue

        # Hard constraint: never recommend an over-budget product.
        if not price.is_finite() or price < 0 or price > budget:
            continue

        product_uses = _get_product_uses(product)
        searchable_text = _get_searchable_text(product)

        matched_uses = sorted(intended_uses & product_uses)

        matched_preferences = sorted(
            preference
            for preference in preferences
            if _preference_matches(preference, searchable_text)
        )

        # Calculate intended-use relevance.
        use_score = (
            len(matched_uses) / len(intended_uses)
            if intended_uses
            else 0.0
        )

        # Calculate preference relevance.
        preference_score = (
            len(matched_preferences) / len(preferences)
            if preferences
            else 0.0
        )

        # Combine the available relevance signals.
        if intended_uses and preferences:
            score = 0.7 * use_score + 0.3 * preference_score
        elif intended_uses:
            score = use_score
        elif preferences:
            score = preference_score
        else:
            score = 0.0

        # Bonus only when a requested specialized use is explicitly
        # listed in the product's intended uses.
        requested_specialized = intended_uses & SPECIALIZED_USES
        matched_specialized = set(matched_uses) & SPECIALIZED_USES

        if requested_specialized:
            specialized_match_ratio = (
                len(matched_specialized) / len(requested_specialized)
            )
            score += 0.3 * specialized_match_ratio

        # Keep the score within the range 0.0 to 1.0.
        score = min(score, 1.0)

        # Build explanations from confirmed catalogue matches.
        reasons = []

        if matched_uses:
            reasons.append(
                "matches intended uses: " + ", ".join(matched_uses)
            )

        if matched_preferences:
            reasons.append(
                "matches listed preferences: "
                + ", ".join(matched_preferences)
            )

        reasons.append(
            f"priced at ₹{price:,.0f}, "
            f"within your ₹{budget:,.0f} budget"
        )

        if not matched_uses and not matched_preferences:
            reasons.insert(
                0,
                "no requested use or preference could be confirmed "
                "from the catalogue",
            )

        results.append(
            {
                "product_id": product.product_id,
                "name": product.name,
                "category": product.category,
                "price": float(price),
                "specifications": (
                    getattr(product, "specifications", None) or {}
                ),
                "score": round(score, 4),
                "matched_uses": matched_uses,
                "matched_preferences": matched_preferences,
                "explanation": (
                    "This product " + "; ".join(reasons) + "."
                ),
            }
        )

    # Rank by relevance first, then price, then product name.
    results.sort(
        key=lambda item: (
            -item["score"],
            item["price"],
            item["name"].lower(),
        )
    )

    return results[:limit]
