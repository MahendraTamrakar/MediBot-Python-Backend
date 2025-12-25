from fastapi import APIRouter, Depends, HTTPException
from core.auth.firebase_auth import get_current_user
from core.services.chat_history_service import ChatHistoryService

router = APIRouter(prefix="/chat-history")

chat_history_service = ChatHistoryService()

@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    firebase_uid: str = Depends(get_current_user)
):
    deleted = await chat_history_service.delete_session(
        firebase_uid,
        session_id
    )

    if deleted == 0:
        raise HTTPException(404, "Chat session not found")

    return {
        "message": "Chat session deleted successfully",
        "session_id": session_id
    }


@router.delete("/all")
async def delete_all_chat_history(
    firebase_uid: str = Depends(get_current_user)
):
    deleted_count = await chat_history_service.delete_all_sessions(firebase_uid)

    return {
        "message": "All chat history deleted successfully",
        "deleted_sessions": deleted_count
    }
