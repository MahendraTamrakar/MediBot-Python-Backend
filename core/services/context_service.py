class ContextService:
    def __init__(self, users_collection):
        self.users = users_collection

    async def build_context(self, firebase_uid: str) -> str:
        """
        Builds contextual information from the user's long-term medical profile.
        """

        user = await self.users.find_one(
            {"firebase_uid": firebase_uid},
            {"_id": 0, "profile": 1}
        )

        if not user or "profile" not in user:
            return "No prior medical history available."

        profile = user["profile"]

        context_parts = []

        if profile.get("age"):
            context_parts.append(f"Age: {profile['age']}")

        if profile.get("gender"):
            context_parts.append(f"Gender: {profile['gender']}")

        if profile.get("allergies"):
            context_parts.append(
                f"Allergies: {', '.join(profile['allergies'])}"
            )

        if profile.get("chronic_conditions"):
            context_parts.append(
                f"Chronic conditions: {', '.join(profile['chronic_conditions'])}"
            )

        if profile.get("active_medications"):
            context_parts.append(
                f"Current medications: {', '.join(profile['active_medications'])}"
            )

        if profile.get("medical_summary"):
            context_parts.append(
                f"Medical summary: {profile['medical_summary']}"
            )

        return "\n".join(context_parts) if context_parts else "No relevant prior context."