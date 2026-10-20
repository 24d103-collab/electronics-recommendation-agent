import json
import re
from decimal import Decimal, InvalidOperation

import ollama


MODEL_NAME = "qwen2.5:3b"

ALLOWED_CATEGORIES = {
    "laptop",
    "smartphone",
    "headphones",
    "monitor",
    "tablet",
    "smartwatch",
    "speaker",
    "router",
}

CATEGORY_PATTERNS = {
    "laptop": r"\b(laptops?|notebooks?)\b",
    "smartphone": r"\b(smartphones?|mobile phones?|mobiles?)\b",
    "headphones": r"\b(headphones?|earbuds?)\b",
    "monitor": r"\b(monitors?|computer screens?)\b",
    "tablet": r"\b(tablets?|ipads?)\b",
    "smartwatch": r"\b(smartwatches?|smart watches?)\b",
    "speaker": r"\b(speakers?)\b",
    "router": r"\b(routers?|wi-?fi routers?)\b",
}

INTENDED_USE_LABELS = {
    "music",
    "online classes",
    "calls",
    "programming",
    "college",
    "gaming",
    "machine learning",
    "office work",
    "photography",
    "study",
    "reading",
    "video streaming",
    "fitness",
    "running",
    "travel",
    "home networking",
    "streaming",
    "light gaming",
    "creative work",
    "everyday use",
    "web browsing",
    "multitasking",
    "note taking",
    "outdoor use",
    "outdoor activities",
    "parties",
    "large homes",
}


def detect_explicit_category(message: str) -> str | None:
    """Return a category explicitly named in the latest message."""
    text = message.lower()
    for category, pattern in CATEGORY_PATTERNS.items():
        if re.search(pattern, text):
            return category
    return None


def normalize_requirement_labels(parsed: dict) -> dict:
    """Move known activities from preferences into intended uses."""
    parsed = dict(parsed)
    uses = parsed.get("intended_uses")
    preferences = parsed.get("preferences")

    normalized_uses = {
        str(value).strip().lower()
        for value in uses
        if isinstance(value, str) and value.strip()
    } if isinstance(uses, list) else set()

    normalized_preferences = {
        str(value).strip().lower()
        for value in preferences
        if isinstance(value, str) and value.strip()
    } if isinstance(preferences, list) else set()

    for label in list(normalized_preferences):
        if label in INTENDED_USE_LABELS:
            normalized_preferences.remove(label)
            normalized_uses.add(label)

    parsed["intended_uses"] = sorted(normalized_uses)
    parsed["preferences"] = sorted(normalized_preferences)
    return parsed


def _valid_string_list(value) -> list[str]:
    """Validate and deduplicate a list of strings."""
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(
        item.strip().lower()
        for item in value
        if isinstance(item, str) and item.strip()
    ))


def _explicit_budget(message: str) -> int | None:
    """Extract a stated budget, including bare amounts such as 'under 80000'."""
    text = message.lower().replace(",", "")

    # Strong signals first: currency prefixes or explicit magnitude suffixes.
    patterns = [
        r"(?:₹|rs\.?\s*|inr\s*)\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|k)?\b",
        r"\b(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|k)\b",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, text))
        if matches:
            match = matches[-1]
            try:
                amount = Decimal(match.group(1))
            except InvalidOperation:
                continue
            unit = (match.group(2) or "").lower()
            if unit == "k":
                amount *= 1000
            elif unit in {"lakh", "lakhs", "lac", "lacs"}:
                amount *= 100000
            if amount > 0:
                return int(amount)

    # Bare numbers are only treated as budgets when tied to budget language.
    # This prevents unrelated model numbers or product sizes from becoming budgets.
    bare_budget_pattern = (
        r"\b(?:under|below|less than|up to|upto|within|budget(?: is| of| around)?|"
        r"maximum|max(?:imum)? price|spend(?:ing)?(?: around| up to)?)\s+"
        r"(?:₹|rs\.?\s*|inr\s*)?(\d{3,9}(?:\.\d+)?)\b"
    )
    matches = list(re.finditer(bare_budget_pattern, text))
    if matches:
        try:
            amount = Decimal(matches[-1].group(1))
        except InvalidOperation:
            return None
        return int(amount) if amount > 0 else None

    return None


def _remove_rejected_items(message: str, items: list[str]) -> list[str]:
    """
    Remove only items named after a rejection phrase.
    Example: 'forget gaming' removes gaming, not programming.
    """
    text = message.lower()
    rejection_patterns = [
        r"\b(?:forget|remove|drop|delete|exclude|without|"
        r"don't want|do not want|no longer want|not interested in)\b"
        r"\s+(?:the\s+)?(.+?)(?=$|[.!?,;]|\bbut\b|\binstead\b)",
    ]

    rejected_text = []
    for pattern in rejection_patterns:
        rejected_text.extend(
            match.group(1).strip()
            for match in re.finditer(pattern, text)
        )

    if not rejected_text:
        return items

    result = []
    for item in items:
        item_norm = item.strip().lower()
        rejected = any(
            re.search(rf"\b{re.escape(item_norm)}\b", phrase)
            for phrase in rejected_text
        )
        if not rejected:
            result.append(item_norm)
    return result


def _explicit_replacement_uses(message: str) -> bool:
    text = message.lower()
    return bool(re.search(
        r"\b(?:only|instead|just|rather than|replace .* with|"
        r"switch to|change .* to)\b",
        text,
    ))


def extract_requirements_with_llm(
    message: str,
    existing_requirements: dict | None = None,
) -> dict:
    """Extract requirements with Ollama and apply deterministic updates."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message must be a non-empty string.")

    existing = dict(existing_requirements or {})

    prompt = f"""
Extract electronics shopping requirements from the latest message.

Return ONLY a JSON object with:
- category: one of {sorted(ALLOWED_CATEGORIES)} or null
- max_budget: positive numeric budget explicitly stated in this message, or null
- intended_uses: list of uses stated or implied by the latest message only
- preferences: list of product preferences stated in the latest message only

Do not copy old requirements into the extracted lists unless the latest message
repeats them. Do not invent requirements. Activities belong in intended_uses.
Physical or product attributes belong in preferences.

Existing context (for interpretation only):
{json.dumps(existing)}

Latest message:
{message}
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract structured shopping requirements. Return valid JSON only. "
                    "Never recommend products or invent facts."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        format="json",
        options={"temperature": 0},
    )

    content = response["message"]["content"]
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("The LLM returned JSON that is not an object.")

    parsed = normalize_requirement_labels(parsed)

    category = parsed.get("category")
    if category not in ALLOWED_CATEGORIES:
        category = None

    budget = parsed.get("max_budget")
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) or budget <= 0:
        budget = None

    new_uses = _valid_string_list(parsed.get("intended_uses"))
    new_preferences = _valid_string_list(parsed.get("preferences"))

    # Start from the saved conversation state.
    merged = dict(existing)

    # Explicit category names always win over model interpretation.
    explicit_category = detect_explicit_category(message)
    if explicit_category is not None:
        merged["category"] = explicit_category
    elif category is not None:
        merged["category"] = category

    # An explicit budget in the latest message always wins over the LLM.
    explicit_budget = _explicit_budget(message)
    if explicit_budget is not None:
        merged["max_budget"] = explicit_budget
    elif budget is not None:
        merged["max_budget"] = budget

    old_uses = _valid_string_list(existing.get("intended_uses", []))
    old_preferences = _valid_string_list(existing.get("preferences", []))
    text = message.lower()

    # Clear an attribute list only when the user explicitly asks to clear it.
    if re.search(r"\b(clear|remove|forget|drop)\s+(all\s+)?(uses|activities)\b", text):
        old_uses = []
    if re.search(r"\b(clear|remove|forget|drop)\s+(all\s+)?(preferences|features)\b", text):
        old_preferences = []

    old_uses = _remove_rejected_items(message, old_uses)
    old_preferences = _remove_rejected_items(message, old_preferences)

    # "Only X" and "X instead" signal replacement rather than accumulation.
    if _explicit_replacement_uses(message) and new_uses:
        merged_uses = new_uses
    else:
        merged_uses = list(dict.fromkeys(old_uses + new_uses))

    merged_uses = _remove_rejected_items(message, merged_uses)

    merged_preferences = list(dict.fromkeys(old_preferences + new_preferences))
    merged_preferences = _remove_rejected_items(message, merged_preferences)

    normalized = normalize_requirement_labels({
        "intended_uses": merged_uses,
        "preferences": merged_preferences,
    })

    merged["intended_uses"] = normalized["intended_uses"]
    merged["preferences"] = normalized["preferences"]

    return merged
