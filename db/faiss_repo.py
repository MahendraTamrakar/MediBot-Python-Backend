from datetime import datetime

class FaissRepository:
    def __init__(self, collection):
        self.collection = collection

    async def save(self, uid, session_id, index_path, document_ids):
        await self.collection.update_one(
            {"firebase_uid": uid, "session_id": session_id},
            {
                "$set": {
                    "index_path": index_path,
                    "document_ids": document_ids,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

    async def delete(self, uid, session_id):
        await self.collection.delete_one(
            {"firebase_uid": uid, "session_id": session_id}
        )
    
    async def delete_all_for_user(self, firebase_uid: str):
        await self.collection.delete_many({
            "firebase_uid": firebase_uid
        })