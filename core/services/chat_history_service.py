from datetime import datetime
from typing import Optional

class ChatHistoryService:
    def __init__(self, collection):
        self.collection = collection

    # ----------------------------------
    # Save a message (per session)
    # ----------------------------------
    async def save_message(
        self,
        firebase_uid: str,
        session_id: str,
        role: str,
        content: str
    ):
        await self.collection.update_one(
            {
                "firebase_uid": firebase_uid,
                "session_id": session_id
            },
            {
                "$push": {
                    "messages": {
                        "role": role,
                        "content": content,
                        "timestamp": datetime.utcnow()
                    }
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

    # ----------------------------------
    # Get a specific session
    # ----------------------------------
    async def get_session(
        self,
        firebase_uid: str,
        session_id: str
    ) -> Optional[dict]:
        return await self.collection.find_one({
            "firebase_uid": firebase_uid,
            "session_id": session_id
        })

    # ----------------------------------
    # Get latest session as plain text
    # (Used for profile update)
    # ----------------------------------
    async def get_recent_chat_text(self, firebase_uid: str) -> str:
        doc = await self.collection.find_one(
            {"firebase_uid": firebase_uid},
            sort=[("created_at", -1)]
        )

        if not doc or "messages" not in doc:
            return ""

        return "\n".join(
            f"{msg['role']}: {msg['content']}"
            for msg in doc["messages"]
        )

    # ----------------------------------
    # Delete a single session
    # ----------------------------------
    async def delete_session(
        self,
        firebase_uid: str,
        session_id: str
    ) -> int:
        result = await self.collection.delete_one({
            "firebase_uid": firebase_uid,
            "session_id": session_id
        })
        return result.deleted_count

    # ----------------------------------
    # Delete all sessions for a user
    # ----------------------------------
    async def delete_all_sessions(self, firebase_uid: str) -> int:
        result = await self.collection.delete_many({
            "firebase_uid": firebase_uid
        })
        return result.deleted_count