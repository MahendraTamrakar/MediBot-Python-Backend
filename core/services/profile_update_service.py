import json
from prompts.profile_update_prompt import build_profile_update_prompt

class ProfileUpdateService:
    def __init__(self, llm, users_collection):
        self.llm = llm
        self.users = users_collection

    async def update_profile(
        self,
        firebase_uid: str,
        chat_history_text: str
    ):
        user = await self.users.find_one({"firebase_uid": firebase_uid})

        current_profile = user.get("profile", {})

        prompt = build_profile_update_prompt(
            current_profile,
            chat_history_text
        )

        raw = await self.llm.generate(prompt)
        updated_profile = json.loads(raw)

        await self.users.update_one(
            {"firebase_uid": firebase_uid},
            {
                "$set": {
                    "profile": updated_profile
                }
            }
        )

        return updated_profile