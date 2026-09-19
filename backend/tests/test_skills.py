import pytest
from app.skills.ship30_writer import build_ship30_prompt
from app.skills.artifact_generator import extract_artifacts

def test_ship30_prompt_formatting():
    retrieved_chunks = [
        {
            "episode": "Adam Mosseri: AI is a tailwind for authenticity",
            "guest": "Adam Mosseri",
            "timestamp": "00:00:23",
            "text": "Taste matters a ton. In a world where it's easier to build things, it's more important to make sure time is spent figuring out what you should be building."
        }
    ]
    query = "How will AI affect product design and taste?"
    prompt = build_ship30_prompt(query, retrieved_chunks)

    assert "Ship 30 for 30" in prompt
    assert "Approximately 1,250 words" in prompt
    assert "The Hook" in prompt
    assert "Adam Mosseri" in prompt
    assert "Taste matters a ton" in prompt
    assert query in prompt

def test_artifact_extraction_html():
    sample_text = """Here is the calculator you requested:

<artifact identifier="growth-loop-calc" type="html" title="Growth Loop Calculator">
<!DOCTYPE html>
<html>
<body><h1>Growth Loop</h1></body>
</html>
</artifact>

Let me know if you need any adjustments to the parameters."""

    cleaned, artifacts = extract_artifacts(sample_text)

    assert len(artifacts) == 1
    art = artifacts[0]
    assert art.identifier == "growth-loop-calc"
    assert art.artifact_type == "html"
    assert art.title == "Growth Loop Calculator"
    assert "<h1>Growth Loop</h1>" in art.content
    assert "<artifact" not in cleaned
    assert "Artifact Created:" in cleaned

def test_artifact_extraction_markdown():
    sample_text = """Here is the PMF guide:

<artifact identifier="pmf-guide" type="markdown" title="Rahul Vohra PMF Guide">
# Superhuman PMF Engine
- Measure 40% very disappointed
</artifact>
"""

    cleaned, artifacts = extract_artifacts(sample_text)

    assert len(artifacts) == 1
    art = artifacts[0]
    assert art.identifier == "pmf-guide"
    assert art.artifact_type == "markdown"
    assert art.title == "Rahul Vohra PMF Guide"
    assert "Superhuman PMF Engine" in art.content
