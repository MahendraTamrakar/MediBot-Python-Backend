from datetime import datetime
from typing import Optional
import uuid

class ChatHistoryService:
    def __init__(self, collection, llm=None):
        self.collection = collection
        self.llm = llm

    # ----------------------------------
    # Generate a new session ID
    # ----------------------------------
    @staticmethod
    def generate_session_id() -> str:
        return str(uuid.uuid4())

    # ----------------------------------
    # Generate title from first message using LLM
    # ----------------------------------
    async def generate_title(self, message: str, max_length: int = 40) -> str:
        """Generate a concise, meaningful title from the user's message using LLM."""
        if not self.llm:
            # Fallback to simple truncation if no LLM
            return self._fallback_title(message, max_length)
        
        try:
            prompt = f"""Generate a short, concise title (max 5 words) for a medical chat session based on this user message. 
Return ONLY the title, nothing else. No quotes, no explanation.

User message: "{message}"

Title:"""
            
            title = await self.llm.generate(prompt)
            title = title.strip().strip('"\'')
            
            # Ensure it's not too long
            if len(title) > max_length:
                title = title[:max_length - 3] + "..."
            
            return title if title else self._fallback_title(message, max_length)
            
        except Exception:
            return self._fallback_title(message, max_length)
    
    @staticmethod
    def _fallback_title(message: str, max_length: int = 40) -> str:
        """Fallback title generation by truncating message."""
        title = message.strip()
        if len(title) > max_length:
            title = title[:max_length - 3] + "..."
        return title

    # ----------------------------------
    # Check if session exists
    # ----------------------------------
    async def session_exists(
        self,
        firebase_uid: str,
        session_id: str
    ) -> bool:
        doc = await self.collection.find_one(
            {
                "firebase_uid": firebase_uid,
                "session_id": session_id
            },
            {"_id": 1}
        )
        return doc is not None

    # ----------------------------------
    # Create a new session
    # ----------------------------------
    async def create_session(
        self,
        firebase_uid: str,
        session_id: str,
        title: str
    ) -> dict:
        now = datetime.utcnow()
        session_doc = {
            "firebase_uid": firebase_uid,
            "session_id": session_id,
            "title": title,
            "messages": [],
            "created_at": now,
            "updated_at": now
        }
        await self.collection.insert_one(session_doc)
        return {
            "session_id": session_id,
            "title": title,
            "created_at": now
        }

    # ----------------------------------
    # Update session title
    # ----------------------------------
    async def update_title(
        self,
        firebase_uid: str,
        session_id: str,
        title: str
    ):
        await self.collection.update_one(
            {
                "firebase_uid": firebase_uid,
                "session_id": session_id
            },
            {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )

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
                "$set": {
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow(),
                    "title": "New Chat"
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
    # List all sessions for a user
    # ----------------------------------
    async def list_sessions(self, firebase_uid: str) -> list:
        cursor = self.collection.find(
            {"firebase_uid": firebase_uid},
            {
                "_id": 0,
                "session_id": 1,
                "title": 1,
                "created_at": 1,
                "updated_at": 1
            }
        ).sort("updated_at", -1)
        
        return await cursor.to_list(length=100)

    # ----------------------------------
    # Get latest session as plain text
    # (Used for profile update)
    # ----------------------------------
    async def get_recent_chat_text(self, firebase_uid: str) -> str:
        doc = await self.collection.find_one(
            {"firebase_uid": firebase_uid},
            sort=[("updated_at", -1)]
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

    # Alias for compatibility
    async def delete(self, firebase_uid: str, session_id: str) -> int:
        return await self.delete_session(firebase_uid, session_id)

    # ----------------------------------
    # Delete all sessions for a user
    # ----------------------------------
    async def delete_all_sessions(self, firebase_uid: str) -> int:
        result = await self.collection.delete_many({
            "firebase_uid": firebase_uid
        })
        return result.deleted_count