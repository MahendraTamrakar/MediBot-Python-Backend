class EmergencyService:
    EMERGENCY_KEYWORDS = [
        "chest pain",
        "difficulty breathing",
        "shortness of breath",
        "fainting",
        "seizure",
        "severe bleeding"
    ]

    def is_emergency(self, text: str) -> bool:
        text = text.lower()
        return any(k in text for k in self.EMERGENCY_KEYWORDS)