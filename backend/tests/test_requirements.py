
from app.agent.requirements import (
    extract_requirements,
    missing_information,
)


def test_extracts_laptop_budget_and_uses():
    result = extract_requirements(
        "I need a laptop for programming and college under 70000"
    )

    assert result["category"] == "laptop"
    assert result["max_budget"] == "70000"
    assert "programming" in result["intended_uses"]
    assert "college" in result["intended_uses"]


def test_updates_existing_requirements():
    existing = {
        "category": "laptop",
        "max_budget": "80000",
        "intended_uses": ["college"],
    }

    result = extract_requirements(
        "My budget is under 60000",
        existing,
    )

    assert result["category"] == "laptop"
    assert result["max_budget"] == "60000"
    assert "college" in result["intended_uses"]


def test_asks_for_category_when_missing():
    question = missing_information({})

    assert question is not None
    assert "type of electronics" in question.lower()


def test_asks_for_use_when_laptop_use_is_missing():
    question = missing_information({
        "category": "laptop",
        "max_budget": "70000",
    })

    assert question is not None
    assert "use" in question.lower()


def test_asks_for_budget_when_missing():
    question = missing_information({
        "category": "laptop",
        "intended_uses": ["programming"],
    })

    assert question is not None
    assert "budget" in question.lower()
