import json
from core.agents.base_agent import BaseAgent
from prompts.diagnosis_prompt import build_diagnosis_prompt
from core.interfaces.llm_interface import LLMInterface

class DiagnosisAgent(BaseAgent):
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    async def run(self, report_text: str) -> dict:
        if not report_text.strip():
            return {"error": "Unable to extract readable data from report"}

        prompt = build_diagnosis_prompt(report_text)
        response = ""

        async for token in self.llm.stream_response(prompt):
            response += token

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "AI could not generate reliable diagnosis"}