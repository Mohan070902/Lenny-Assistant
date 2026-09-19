import re
from typing import List, Optional, Tuple
from app.models.schemas import ArtifactBase

ARTIFACT_SYSTEM_INSTRUCTION = """
### Artifact Generation Guidelines:
When the user asks for reusable content, diagrams, interactive widgets, calculators, frameworks, or standalone documents, you should generate an **Artifact**.
To create an artifact, wrap the content in XML tags with the following attributes:
- `identifier`: A kebab-case unique slug (e.g. `growth-cac-calculator`, `pmf-survey-template`).
- `type`: Must be either `markdown` or `html`.
- `title`: A concise, human-readable title.

Example for HTML/CSS Artifact:
<artifact identifier="churn-calculator" type="html" title="SaaS Churn & LTV Calculator">
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Calculator</title>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #f8fafc; color: #1e293b; }
    .card { background: white; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); max-width: 500px; margin: auto; }
    input, button { width: 100%; padding: 10px; margin-top: 8px; border-radius: 6px; border: 1px solid #cbd5e1; }
    button { background: #6366f1; color: white; border: none; font-weight: bold; cursor: pointer; }
  </style>
</head>
<body>
  <div class="card">
    <h2>SaaS Churn Calculator</h2>
    <label>Monthly Churn Rate (%): <input id="churn" type="number" value="3.5" step="0.1" /></label>
    <label>ARPU ($): <input id="arpu" type="number" value="120" /></label>
    <button onclick="calculate()">Compute Customer Lifetime</button>
    <h3 id="result"></h3>
  </div>
  <script>
    function calculate() {
      const churn = parseFloat(document.getElementById('churn').value) / 100;
      const arpu = parseFloat(document.getElementById('arpu').value);
      if (churn > 0) {
        const lifetimeMonths = (1 / churn).toFixed(1);
        const ltv = (arpu * (1 / churn)).toFixed(2);
        document.getElementById('result').innerText = 'Avg Lifetime: ' + lifetimeMonths + ' months | LTV: $' + ltv;
      }
    }
  </script>
</body>
</html>
</artifact>

Example for Markdown Artifact:
<artifact identifier="pmf-framework" type="markdown" title="Rahul Vohra 4-Step PMF Engine">
# The 4-Step PMF Engine
...
</artifact>

Provide helpful conversational text before or after the artifact tag explaining what was built and how to use it.
"""

ARTIFACT_REGEX = re.compile(
    r'<artifact\s+identifier=["\']([^"\']+)["\']\s+type=["\']([^"\']+)["\']\s+title=["\']([^"\']+)["\']>(.*?)</artifact>',
    re.DOTALL | re.IGNORECASE
)

def extract_artifacts(text: str) -> Tuple[str, List[ArtifactBase]]:
    """
    Extract artifacts from LLM response text.
    Returns:
        cleaned_text: text without raw artifact body (or with a clean placeholder)
        artifacts: list of ArtifactBase objects
    """
    artifacts = []
    
    def replacer(match):
        ident = match.group(1).strip()
        atype = match.group(2).strip().lower()
        title = match.group(3).strip()
        content = match.group(4).strip()
        
        # Normalize artifact type
        if atype not in ["html", "markdown"]:
            atype = "markdown"

        artifacts.append(ArtifactBase(
            identifier=ident,
            title=title,
            artifact_type=atype,
            content=content
        ))
        return f"\n\n> 📦 **Artifact Created:** [{title}] (Type: `{atype}`) — *Click to view in the side panel*\n\n"

    cleaned_text = ARTIFACT_REGEX.sub(replacer, text)
    return cleaned_text, artifacts
