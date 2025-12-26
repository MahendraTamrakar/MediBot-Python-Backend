from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
import logging

# Auth
from core.auth.dependencies import get_current_user

# Services
from core.services.chat_service import ChatService
from core.services.emergency_service import EmergencyService
from core.services.context_service import ContextService
from core.services.followup_service import FollowUpService
from core.services.compliance_service import ComplianceService
from core.services.profile_update_service import ProfileUpdateService
from core.services.chat_history_service import ChatHistoryService


# Infrastructure & DB
from infrastructure.llm.gemini_llm import GeminiLLM
from db.mongodb import users_collection, chat_sessions_collection
from db.users_repo import ensure_user_exists

router = APIRouter()
logger = logging.getLogger(__name__)

# ----------------------------
# Initialize dependencies ONCE
# ----------------------------
llm = GeminiLLM()

chat_history_service = ChatHistoryService(chat_sessions_collection)

chat_service = ChatService(
    llm=llm,
    emergency=EmergencyService(),
    context_service=ContextService(users_collection),
    followup=FollowUpService(),
    compliance=ComplianceService(),
    chat_history=chat_history_service
)

profile_update_service = ProfileUpdateService(
    llm=llm,
    users_collection=users_collection
)

# ----------------------------
# Request Models
# ----------------------------
class ChatRequest(BaseModel):
    symptoms: str = Field(..., min_length=1, max_length=1000)

# ----------------------------
# API Endpoints
# ----------------------------

@router.post("/analyze-symptoms", status_code=status.HTTP_200_OK)
async def analyze(
    req: ChatRequest,
    firebase_uid: str = Depends(get_current_user)
):
    try:
        await ensure_user_exists(users_collection, firebase_uid)
        return await chat_service.analyze(firebase_uid, req.symptoms)

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("Unexpected server error in analyze")
        raise HTTPException(status_code=500, detail="An error occurred.")


@router.post("/end-chat", status_code=status.HTTP_200_OK)
async def end_chat(
    firebase_uid: str = Depends(get_current_user)
):
    """
    Called when user leaves chat.
    Triggers profile update from stored chat history.
    """
    try:
        # 1. Fetch recent chat history from MongoDB
        chat_text = await chat_history_service.get_recent_chat_text(firebase_uid)

        if not chat_text:
            return {
                "message": "No chat history found",
                "profile_updated": False
            }

        # 2. Update long-term medical profile
        updated_profile = await profile_update_service.update_profile(
            firebase_uid=firebase_uid,
            chat_history_text=chat_text
        )

        return {
            "message": "Profile updated successfully",
            "profile": updated_profile
        }

    except Exception as e:
        logger.exception(f"Profile update failed for user {firebase_uid}")

        # IMPORTANT: Do NOT crash UI
        return {
            "message": "Chat ended, but profile update failed",
            "profile_updated": False
        }

@router.delete("/chats", status_code=status.HTTP_200_OK)
async def delete_all_chats(
    firebase_uid: str = Depends(get_current_user)
):
    try:
        deleted_count = await chat_history_service.delete_all_sessions(firebase_uid)

        return {
            "message": "All chat history deleted",
            "deleted_sessions": deleted_count
        }

    except Exception:
        logger.exception("Failed to delete chat history")
        raise HTTPException(500, "Failed to delete chat history")
    
@router.delete("/chats/{session_id}", status_code=status.HTTP_200_OK)
async def delete_chat_session(
    session_id: str,
    firebase_uid: str = Depends(get_current_user)
):
    deleted = await chat_history_service.delete_session(firebase_uid, session_id)

    if deleted == 0:
        raise HTTPException(404, "Session not found")

    return {
        "message": "Chat session deleted",
        "session_id": session_id
    }