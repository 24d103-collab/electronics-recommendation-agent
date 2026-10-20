
from app.agent.llm_service import normalize_requirement_labels


def test_music_is_an_intended_use_not_a_preference():
    result = normalize_requirement_labels({
        "intended_uses": ["online classes"],
        "preferences": ["music", "good noise isolation"],
    })

    assert "music" in result["intended_uses"]
    assert "online classes" in result["intended_uses"]
    assert "music" not in result["preferences"]
    assert "good noise isolation" in result["preferences"]


def test_empty_fields_are_supported():
    result = normalize_requirement_labels({})

    assert result["intended_uses"] == []
    assert result["preferences"] == []
