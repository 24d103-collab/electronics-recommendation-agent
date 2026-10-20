
import re
from decimal import Decimal


def extract_requirements(
    message: str,
    existing: dict | None = None,
) -> dict:
    """
    Extract basic requirements from a customer message.

    New explicitly detected values update previous values.
    This is a starter parser, not a complete natural-language model.
    """
    requirements = dict(existing or {})
    text = message.lower()

    # Category
    categories = {
        "laptop": ["laptop", "notebook"],
        "smartphone": ["phone", "smartphone", "mobile"],
        "headphones": ["headphone", "headphones", "earbuds"],
        "monitor": ["monitor", "display"],
    }

    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            requirements["category"] = category
            break

    # Budget, e.g. "under 70000", "budget 80000", "₹75,000"
    budget_patterns = [
        r"(?:under|below|less than|maximum|max|budget(?:\s+of)?|around)\s*₹?\s*([\d,]+)",
        r"₹\s*([\d,]+)",
    ]

    for pattern in budget_patterns:
        match = re.search(pattern, text)
        if match:
            amount = match.group(1).replace(",", "")
            requirements["max_budget"] = str(Decimal(amount))
            break

    # Intended use
    uses = {
        "programming": ["programming", "coding", "development"],
        "machine learning": ["machine learning", "ml", "local models"],
        "gaming": ["gaming", "games", "play games"],
        "college": ["college", "university", "student", "classes"],
        "office work": ["office", "productivity", "spreadsheets"],
        "creative work": ["video editing", "photo editing", "design"],
    }

    detected_uses = set(requirements.get("intended_uses", []))
    for use, keywords in uses.items():
        if any(keyword in text for keyword in keywords):
            detected_uses.add(use)

    if detected_uses:
        requirements["intended_uses"] = sorted(detected_uses)

    return requirements


def missing_information(requirements: dict) -> str | None:
    """Return one focused question when essential details are missing."""
    if not requirements.get("category"):
        return "Which type of electronics are you looking for?"

    if requirements["category"] == "laptop" and not requirements.get("intended_uses"):
        return "What will you mainly use the laptop for?"

    if not requirements.get("max_budget"):
        return "What is your maximum budget in rupees?"

    return None
