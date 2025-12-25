class FollowUpService:
    BASE_QUESTIONS = {
        "fever": [
            "How many days have you had the fever?",
            "Is the fever continuous or intermittent?"
        ],
        "headache": [
            "Is the headache mild or severe?",
            "Do you have sensitivity to light or sound?"
        ],
        "cough": [
            "Is the cough dry or with mucus?",
            "Are you experiencing throat irritation?"
        ],
        "stomach pain": [
            "Is the pain sharp or dull?",
            "Have you experienced nausea or vomiting?"
        ]
    }

    def generate_questions(self, symptoms: str, severity: str):
        questions = []
        symptoms_lower = symptoms.lower()

        for key, qs in self.BASE_QUESTIONS.items():
            if key in symptoms_lower:
                questions.extend(qs)

        # Severity-based generic follow-ups
        if severity == "medium":
            questions.append("Have these symptoms affected your daily activities?")
        elif severity == "low":
            questions.append("Are the symptoms improving or staying the same?")

        # Limit number of questions (UX-friendly)
        return questions[:3]