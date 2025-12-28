import os
from typing import List, Dict
from fastapi import HTTPException

from db.mongodb import (
    client,
    users_collection,
    medical_reports_collection,
    chat_sessions_collection,
    faiss_indexes_collection,
)

class AccountDeletionService:
    """
    Coordinates a hard delete of a user's account and all associated data.
    - Removes filesystem FAISS index files recorded in metadata
    - Uses a MongoDB transaction to remove user, reports, chats, and FAISS metadata
    """

    async def _get_user_faiss_index_paths(self, firebase_uid: str) -> List[str]:
        paths: List[str] = []
        cursor = faiss_indexes_collection.find({"firebase_uid": firebase_uid}, {"index_path": 1})
        async for doc in cursor:
            p = doc.get("index_path")
            if isinstance(p, str) and p:
                paths.append(p)
        return paths

    async def _delete_files(self, paths: List[str]) -> List[Dict[str, str]]:
        """Attempt to delete files recorded in FAISS metadata. Returns error list if any."""
        errors: List[Dict[str, str]] = []
        for p in paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
                # If file doesn't exist, treat as success (no orphan will remain after DB delete)
            except Exception as e:
                errors.append({"path": p, "error": str(e)})
        return errors

    async def delete_user_account(self, firebase_uid: str) -> Dict:
        """
        Hard delete the user and all related data.
        Steps:
        1) Collect FAISS file paths for the user
        2) Delete files; if any failure, abort
        3) Execute transactional MongoDB delete across collections
        """
        # 1) Collect index file paths
        paths = await self._get_user_faiss_index_paths(firebase_uid)

        # 2) Delete files first to avoid leaving metadata pointing at non-existent files
        file_errors = await self._delete_files(paths)
        if file_errors:
            raise HTTPException(status_code=500, detail={
                "message": "Failed to delete some index files",
                "errors": file_errors
            })

        # 3) Transactional DB delete (best effort; requires replica set)
        try:
            async with await client.start_session() as session:
                async with session.start_transaction():
                    await users_collection.delete_one({"firebase_uid": firebase_uid}, session=session)
                    await medical_reports_collection.delete_many({"firebase_uid": firebase_uid}, session=session)
                    await chat_sessions_collection.delete_many({"firebase_uid": firebase_uid}, session=session)
                    await faiss_indexes_collection.delete_many({"firebase_uid": firebase_uid}, session=session)
        except Exception:
            # Fallback: non-transactional delete if transactions unsupported
            await users_collection.delete_one({"firebase_uid": firebase_uid})
            await medical_reports_collection.delete_many({"firebase_uid": firebase_uid})
            await chat_sessions_collection.delete_many({"firebase_uid": firebase_uid})
            await faiss_indexes_collection.delete_many({"firebase_uid": firebase_uid})

        return {
            "deleted_user": True,
            "deleted_reports": True,
            "deleted_chat_sessions": True,
            "deleted_faiss_metadata": True,
            "deleted_index_files": len(paths),
        }
