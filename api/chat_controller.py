from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import json

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
from core.services.faiss_service import FaissService
from core.services.memory.redis_chat_memory import RedisChatMemory
from core.services.vector.embedding_service import EmbeddingService

# Infrastructure & DB
from infrastructure.llm.gemini_llm import GeminiLLM
from db.mongodb import users_collection, chat_sessions_collection
from db.users_repo import ensure_user_exists
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# ----------------------------
# Initialize dependencies ONCE
# ----------------------------
llm = GeminiLLM()

# Initialize Redis memory
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_memory = RedisChatMemory(url=redis_url)

# Initialize FAISS service
faiss_service = FaissService(base_path="faiss_store")

# Initialize embedding service
embedding_service = EmbeddingService(llm=llm)

chat_history_service = ChatHistoryService(chat_sessions_collection, llm=llm)

chat_service = ChatService(
    llm=llm,
    emergency=EmergencyService(),
    context_service=ContextService(users_collection),
    redis_memory=redis_memory,
    faiss_service=faiss_service,
    embedding_service=embedding_service,
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
    session_id: str | None = Field(default=None, min_length=1, max_length=100)
    symptoms: str = Field(..., min_length=1, max_length=1000)

# ----------------------------
# Helper: Ensure session exists or create it
# ----------------------------
async def ensure_session(
    firebase_uid: str,
    session_id: str | None,
    first_message: str
) -> tuple[str, str | None, bool]:
    """
    Ensures a chat session exists. Creates one if needed.
    
    Returns:
        (session_id, title, is_new_session)
    """
    # Generate session_id if not provided
    if not session_id:
        session_id = chat_history_service.generate_session_id()
        title = await chat_history_service.generate_title(first_message)
        await chat_history_service.create_session(firebase_uid, session_id, title)
        return session_id, title, True
    
    # Check if session exists
    exists = await chat_history_service.session_exists(firebase_uid, session_id)
    if not exists:
        title = await chat_history_service.generate_title(first_message)
        await chat_history_service.create_session(firebase_uid, session_id, title)
        return session_id, title, True
    
    return session_id, None, False

# ----------------------------
# Helper: Streaming generator wrapper
# ----------------------------
async def stream_with_history(
    firebase_uid: str,
    session_id: str,
    user_message: str,
    is_document_mode: bool,
    session_info: dict | None = None
):
    """
    Generator that:
    1. Streams tokens from chat service
    2. Collects full response
    3. Saves to MongoDB and Redis after stream completes
    """
    full_response = ""
    
    try:
        # If new session, send session info first
        if session_info:
            yield f"data: {json.dumps({'session': session_info})}\n\n".encode('utf-8')
        
        # Stream response
        async for chunk in chat_service.stream_analyze(firebase_uid, session_id, user_message):
            full_response += chunk
            # Yield with newline for streaming protocol
            yield f"data: {json.dumps({'token': chunk})}\n\n".encode('utf-8')
        
        # After streaming completes, save full response to history and Redis
        await chat_history_service.save_message(
            firebase_uid, session_id, "assistant", full_response
        )
        await redis_memory.save_message(
            firebase_uid, session_id, "assistant", full_response
        )
        
        # Send completion signal
        yield f"data: {json.dumps({'done': True, 'type': 'document_chat' if is_document_mode else 'medical_chat'})}\n\n".encode('utf-8')
        
    except Exception as e:
        logger.exception("Error in stream_with_history")
        yield f"data: {json.dumps({'error': str(e)})}\n\n".encode('utf-8')

# ----------------------------
# API Endpoints
# ----------------------------

@router.post("/analyze-symptoms", status_code=status.HTTP_200_OK)
async def analyze(
    req: ChatRequest,
    firebase_uid: str = Depends(get_current_user)
):
    """Non-streaming endpoint with auto session creation."""
    try:
        await ensure_user_exists(users_collection, firebase_uid)
        
        # Ensure session exists or create it
        session_id, title, is_new = await ensure_session(
            firebase_uid, req.session_id, req.symptoms
        )
        
        # Get chat response
        response = await chat_service.analyze(firebase_uid, session_id, req.symptoms)
        
        # Include session info in response
        result = {
            "session_id": session_id,
            **response
        }
        
        if is_new and title:
            result["title"] = title
        
        return result

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("Unexpected server error in analyze")
        raise HTTPException(status_code=500, detail="An error occurred.")

@router.post("/analyze-symptoms/stream", status_code=200)
async def analyze_stream(
    req: ChatRequest,
    firebase_uid: str = Depends(get_current_user)
):
    """Streaming endpoint with auto session creation."""
    try:
        await ensure_user_exists(users_collection, firebase_uid)
        
        # Ensure session exists or create it
        session_id, title, is_new = await ensure_session(
            firebase_uid, req.session_id, req.symptoms
        )
        
        # Check if documents exist for this session (for response type)
        is_document_mode = faiss_service.has_documents(firebase_uid, session_id)
        
        # Prepare session info for new sessions
        session_info = None
        if is_new:
            session_info = {"session_id": session_id, "title": title}
        
        return StreamingResponse(
            stream_with_history(firebase_uid, session_id, req.symptoms, is_document_mode, session_info),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("Unexpected server error in analyze stream")
        raise HTTPException(status_code=500, detail="An error occurred.")

@router.get("/chats", status_code=200)
async def list_chats(
    firebase_uid: str = Depends(get_current_user)
):
    """
    Returns all past chat sessions for the user with title
    """
    sessions = await chat_history_service.list_sessions(firebase_uid)
    return sessions

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

""" @router.delete("/chats", status_code=status.HTTP_200_OK)
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
        raise HTTPException(500, "Failed to delete chat history") """

@router.delete("/chats", status_code=status.HTTP_200_OK)
async def delete_all_chats(
    firebase_uid: str = Depends(get_current_user)
):
    """
    Deletes ALL chat history for the user:
    - MongoDB chat sessions
    - Redis chat memory
    - FAISS indexes
    - FAISS metadata
    """
    try:
        # 1. MongoDB
        deleted_count = await chat_history_service.delete_all_sessions(firebase_uid)

        # 2. Redis
        await redis_memory.clear_all_for_user(firebase_uid)

        # 3. FAISS indexes
        faiss_service.delete_all_for_user(firebase_uid)

        return {
            "message": "All chat history deleted successfully",
            "deleted_sessions": deleted_count
        }

    except Exception:
        logger.exception("Failed to delete all chat history")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete all chat history"
        )
@router.get("/chats/{session_id}/messages", status_code=200)
async def get_chat_messages(
    session_id: str,
    firebase_uid: str = Depends(get_current_user)
):
    chat = await chat_sessions_collection.find_one(
        {
            "firebase_uid": firebase_uid,
            "session_id": session_id
        },
        {"_id": 0, "messages": 1}
    )

    if not chat:
        raise HTTPException(404, "Chat not found")

    return chat["messages"]

@router.delete("/chats/{session_id}", status_code=status.HTTP_200_OK)
async def delete_chat_session(
    session_id: str,
    firebase_uid: str = Depends(get_current_user)
):
    await chat_history_service.delete(firebase_uid, session_id)
    await redis_memory.clear(firebase_uid, session_id)
    faiss_service.delete(firebase_uid, session_id)

    return {
        "message": "Chat session deleted",
        "session_id": session_id
    }