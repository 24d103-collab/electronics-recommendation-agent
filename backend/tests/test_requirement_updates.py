
from app.agent.llm_service import extract_requirements_with_llm


def test_category_change_preserves_budget():
    existing = {
        "category": "headphones",
        "max_budget": 3000,
        "intended_uses": ["music"],
        "preferences": ["noise isolation"],
    }

    result = extract_requirements_with_llm(
        "Actually, show me smartphones instead.",
        existing,
    )

    assert result["category"] == "smartphone"
    assert float(result["max_budget"]) == 3000


def test_budget_change_preserves_category():
    existing = {
        "category": "smartphone",
        "max_budget": 30000,
        "intended_uses": ["photography"],
        "preferences": [],
    }

    result = extract_requirements_with_llm(
        "My budget is now 20000 rupees.",
        existing,
    )

    assert result["category"] == "smartphone"
    assert float(result["max_budget"]) == 20000


def test_preference_removal():
    existing = {
        "category": "headphones",
        "max_budget": 3000,
        "intended_uses": ["music"],
        "preferences": ["noise isolation"],
    }

    result = extract_requirements_with_llm(
        "Forget the noise isolation preference.",
        existing,
    )

    assert "noise isolation" not in result.get("preferences", [])
