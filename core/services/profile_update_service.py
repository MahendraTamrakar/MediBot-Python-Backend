import json
from datetime import datetime
from prompts.profile_update_prompt import build_profile_update_prompt


class ProfileUpdateService:
    def __init__(self, llm, users_collection):
        self.llm = llm
        self.users = users_collection

    # -------------------------------------------------
    # 1️⃣ Chat-based profile update (existing, fixed)
    # -------------------------------------------------
    async def update_profile(
        self,
        firebase_uid: str,
        chat_history_text: str
    ):
        user = await self.users.find_one({"firebase_uid": firebase_uid}) or {}
        current_profile = user.get("profile", {})

        prompt = build_profile_update_prompt(
            current_profile,
            chat_history_text
        )

        raw = await self.llm.generate(prompt)

        try:
            updated_profile = json.loads(raw)
        except json.JSONDecodeError:
            # Safety fallback – do not overwrite profile on bad AI output
            return current_profile

        await self.users.update_one(
            {"firebase_uid": firebase_uid},
            {
                "$set": {
                    "profile": updated_profile,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        return updated_profile

    # -------------------------------------------------
    # 2️⃣ NEW: Report-based profile enrichment
    # -------------------------------------------------
    async def merge_report_into_profile(
        self,
        firebase_uid: str,
        report_analysis: dict
    ):
        """
        Safely attaches report insights to the user's medical profile.
        Must be called ONLY after explicit user consent.
        """

        summary = report_analysis.get("summary", "").strip()

        if not summary:
            return False

        await self.users.update_one(
            {"firebase_uid": firebase_uid},
            {
                "$push": {
                    "profile.reports_summary": {
                        "text": summary,
                        "source": "medical_report",
                        "added_at": datetime.utcnow()
                    }
                },
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        return True