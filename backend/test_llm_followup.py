
from app.agent.llm_service import extract_requirements_with_llm

existing = {
    "category": "headphones",
    "max_budget": 3000,
    "intended_uses": ["music", "online classes"],
    "preferences": [],
}

result = extract_requirements_with_llm(
    "I also want good noise isolation",
    existing,
)

print(result)

assert result["category"] == "headphones"
assert float(result["max_budget"]) == 3000
assert "music" in result["intended_uses"]
assert "online classes" in result["intended_uses"]
assert any(
    "noise isolation" in preference.lower()
    for preference in result["preferences"]
)

print("PASS: Follow-up preserved existing requirements.")
