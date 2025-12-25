class ComplianceService:
    def disclaimer(self):
        return (
            "⚠️ Medical Disclaimer: I am not a medical professional. "
            "This information is for educational purposes only and "
            "should not be considered a medical diagnosis."
        )

    def normalize_list(self, value):
        return value if isinstance(value, list) else []