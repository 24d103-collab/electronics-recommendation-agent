
from app.agent.llm_service import extract_requirements_with_llm


message = (
    "I need headphones for music and online classes "
    "under 3000 rupees"
)

result = extract_requirements_with_llm(message)

print(result)

assert result["category"] == "headphones"
assert result["max_budget"] == 3000
assert isinstance(result["intended_uses"], list)

print("PASS: LLM extracted the expected requirements.")
