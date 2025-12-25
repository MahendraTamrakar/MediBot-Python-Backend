from core.agents.base_agent import BaseAgent

class ComplianceAgent(BaseAgent):
    async def run(self, data: dict) -> dict:
        data["ai_disclaimer"] = (
            "I am an AI system and may be incorrect. "
            "This information is not a medical diagnosis. "
            "Always consult a qualified healthcare professional."
        )
        return data
