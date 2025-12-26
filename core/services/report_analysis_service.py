import json

class ReportAnalysisService:
    def __init__(self, llm):
        self.llm = llm

    async def analyze(self, report_text: str):
        prompt = f"""
You are a medical report explainer.

STRICT RULES:
- NO diagnosis
- Explain in simple language
- Highlight abnormal findings
- Always include disclaimer
- OUTPUT JSON ONLY (no markdown)

Report text:
\"\"\"{report_text}\"\"\"

JSON FORMAT:
{{
  "summary": "string",
  "key_findings": {{}},
  "what_is_normal": [],
  "what_needs_attention": [],
  "disclaimer": "string"
}}
"""
        raw = await self.llm.generate(prompt)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Safety fallback (VERY IMPORTANT)
            return {
                "summary": "Unable to analyze the report reliably.",
                "key_findings": {},
                "what_is_normal": [],
                "what_needs_attention": [],
                "disclaimer": "This is not a medical diagnosis. Please consult a doctor."
            }