
from decimal import Decimal
from types import SimpleNamespace

from app.services.recommendation_service import recommend_products


def make_product(
    product_id,
    name,
    price,
    intended_uses,
    category="laptop",
    is_available=True,
):
    return SimpleNamespace(
        product_id=product_id,
        name=name,
        price=Decimal(str(price)),
        intended_uses=intended_uses,
        category=category,
        is_available=is_available,
        specifications={},
    )


def test_rejects_products_above_budget(monkeypatch):
    products = [
        make_product("LAP-001", "Affordable", 50000, ["programming"]),
        make_product("LAP-002", "Too expensive", 80000, ["programming"]),
    ]

    monkeypatch.setattr(
        "app.services.recommendation_service.list_products",
        lambda *args, **kwargs: (products, len(products)),
    )

    results = recommend_products(
        None,
        {
            "category": "laptop",
            "max_budget": "70000",
            "intended_uses": ["programming"],
        },
    )

    assert [p["product_id"] for p in results] == ["LAP-001"]


def test_excludes_unavailable_products(monkeypatch):
    products = [
        make_product(
            "LAP-001", "Unavailable", 50000,
            ["programming"], is_available=False
        ),
    ]

    monkeypatch.setattr(
        "app.services.recommendation_service.list_products",
        lambda *args, **kwargs: (products, len(products)),
    )

    results = recommend_products(
        None,
        {
            "category": "laptop",
            "max_budget": "70000",
            "intended_uses": ["programming"],
        },
    )

    assert results == []


def test_returns_no_matches_when_category_differs(monkeypatch):
    products = [
        make_product(
            "MON-001", "Monitor", 20000, ["office work"],
            category="monitor"
        ),
    ]

    monkeypatch.setattr(
        "app.services.recommendation_service.list_products",
        lambda *args, **kwargs: (products, len(products)),
    )

    results = recommend_products(
        None,
        {
            "category": "laptop",
            "max_budget": "70000",
            "intended_uses": ["programming"],
        },
    )

    assert results == []


def test_returns_empty_without_required_information():
    assert recommend_products(
        None,
        {"category": "laptop"},
    ) == []
