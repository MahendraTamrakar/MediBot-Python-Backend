from core.interfaces.safety_interface import SafetyInterface

class MedicalSafetyService(SafetyInterface):
    def is_allowed(self, text: str) -> bool:
        blocked = ["exact diagnosis", "guaranteed cure", "prescription"]
        return not any(word in text.lower() for word in blocked)

    def disclaimer(self) -> str:
        return (
            "\n\n⚠️ **Medical Disclaimer:**\n"
            "I am not a medical professional. The information provided is for "
            "educational purposes only and should not be considered a medical diagnosis. "
            "Please consult a qualified doctor for professional advice.\n"
        )
