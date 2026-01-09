import json
from prompts.medical_prompt import build_unified_chat_prompt


class ChatService:
    def __init__(
        self,
        llm,
        emergency,
        context_service,
        redis_memory,
        faiss_service,
        embedding_service,
        followup,
        compliance,
        chat_history
    ):
        self.llm = llm
        self.emergency = emergency
        self.context_service = context_service
        self.redis = redis_memory
        self.faiss = faiss_service
        self.embedder = embedding_service
        self.followup = followup
        self.compliance = compliance
        self.chat_history = chat_history

    async def analyze(
        self,
        firebase_uid: str,
        session_id: str,
        message: str
    ):
        """
        Unified chat pipeline with conversation continuity.
        
        - Always uses unified prompt (no conditional switching)
        - Enforces Redis memory for conversation context
        - Returns plain conversational text
        """

        # Save user message to Redis (plain text format)
        await self.redis.save_message(firebase_uid, session_id, "user", message)
        
        # Save user message to MongoDB history
        await self.chat_history.save_message(
            firebase_uid=firebase_uid,
            session_id=session_id,
            role="user",
            content=message
        )

        # Emergency override - use enhanced emergency detection
        if self.emergency.is_emergency(message):
            return await self._handle_emergency(firebase_uid, session_id, message)

        # Get conversation history from Redis (plain text)
        conversation_history = await self.redis.get_conversation_history(
            firebase_uid, session_id, limit=10
        )
        
        # Get user profile context
        profile_context = await self.context_service.build_context(firebase_uid)
        
        # Get document context if available
        document_context = await self._get_document_context(
            firebase_uid, session_id, message
        )

        # Build unified prompt with strong continuity enforcement
        prompt = build_unified_chat_prompt(
            user_message=message,
            conversation_history=conversation_history,
            user_profile=profile_context,
            document_context=document_context
        )

        # Generate plain text response
        response_text = await self._generate_plain_response(prompt)

        # Save assistant response to Redis (plain text format)
        await self.redis.save_message(firebase_uid, session_id, "assistant", response_text)
        
        # Save to MongoDB history
        await self.chat_history.save_message(
            firebase_uid, session_id, "assistant", response_text
        )

        return {
            "session_id": session_id,
            "type": "medical_chat",
            "message": response_text
        }

    async def stream_analyze(
        self,
        firebase_uid: str,
        session_id: str,
        message: str
    ):
        """
        Streaming chat pipeline with conversation continuity.
        Yields text tokens as they arrive from the LLM.
        """

        # Save user message to Redis (plain text format)
        await self.redis.save_message(firebase_uid, session_id, "user", message)
        
        # Save user message to MongoDB history
        await self.chat_history.save_message(
            firebase_uid=firebase_uid,
            session_id=session_id,
            role="user",
            content=message
        )

        # Emergency override - use enhanced emergency detection
        emergency_response = self.emergency.get_emergency_response(message)
        if emergency_response["is_emergency"]:
            response_text = emergency_response["message"]
            yield response_text
            await self.redis.save_message(firebase_uid, session_id, "assistant", response_text)
            await self.chat_history.save_message(firebase_uid, session_id, "assistant", response_text)
            return

        # Get conversation history from Redis (plain text)
        conversation_history = await self.redis.get_conversation_history(
            firebase_uid, session_id, limit=10
        )
        
        # Get user profile context
        profile_context = await self.context_service.build_context(firebase_uid)
        
        # Get document context if available
        document_context = await self._get_document_context(
            firebase_uid, session_id, message
        )

        # Build unified prompt with strong continuity enforcement
        prompt = build_unified_chat_prompt(
            user_message=message,
            conversation_history=conversation_history,
            user_profile=profile_context,
            document_context=document_context
        )

        # Stream response
        full_response = ""
        async for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield chunk

        # Save complete response to Redis and MongoDB after streaming
        await self.redis.save_message(firebase_uid, session_id, "assistant", full_response)
        await self.chat_history.save_message(firebase_uid, session_id, "assistant", full_response)

    async def _handle_emergency(self, firebase_uid: str, session_id: str, user_message: str) -> dict:
        """Handle emergency situations with immediate response using enhanced detection."""
        emergency_response = self.emergency.get_emergency_response(user_message)
        message = emergency_response["message"]
        
        # Add emergency resources if critical
        if emergency_response["urgency_level"] == "critical":
            resources = self.emergency.get_emergency_resources()
            resources_text = "\n\n**Emergency Numbers:**\n" + "\n".join(
                [f"• {region}: {number}" for region, number in resources.items()]
            )
            message += resources_text

        await self.redis.save_message(firebase_uid, session_id, "assistant", message)
        await self.chat_history.save_message(
            firebase_uid, session_id, "assistant", message
        )

        return {
            "session_id": session_id,
            "type": "medical_chat",
            "message": message,
            "urgency_level": emergency_response["urgency_level"],
            "matched_keywords": emergency_response["matched_keywords"]
        }

    async def _get_document_context(
        self,
        firebase_uid: str,
        session_id: str,
        message: str
    ) -> str:
        """
        Get document context if documents exist for this session.
        Returns formatted document chunks or "No document provided."
        """
        # Check if documents exist for this session
        has_documents = self.faiss.has_documents(firebase_uid, session_id)
        
        if not has_documents:
            return "No document provided."
        
        try:
            # Search for relevant document chunks
            query_embedding = await self.embedder.embed(message)
            faiss_results = self._search_document_store(
                firebase_uid, session_id, query_embedding
            )
            
            if not faiss_results:
                return "Document uploaded but no relevant sections found for this query."
            
            # Format document chunks
            chunks = []
            for chunk in faiss_results[:5]:
                if isinstance(chunk, dict):
                    chunks.append(chunk.get("text", str(chunk)))
                else:
                    chunks.append(str(chunk))
            
            return "\n\n".join(chunks)
        except Exception as e:
            return f"Document context unavailable: {str(e)}"

    def _search_document_store(self, uid: str, session_id: str, query_embedding: list) -> list:
        """
        Search the document vector store for relevant chunks.
        Handles both FaissService and FaissVectorStore patterns.
        """
        import os
        import pickle
        import faiss
        import numpy as np

        # Try document-specific index first (created by upload-document)
        doc_index_path = f"{self.faiss.base_path}/{uid}_{session_id}_docs.index"
        meta_path = doc_index_path + ".meta"

        if os.path.exists(doc_index_path) and os.path.exists(meta_path):
            try:
                index = faiss.read_index(doc_index_path)
                with open(meta_path, "rb") as f:
                    metadata = pickle.load(f)

                if not query_embedding:
                    return []

                D, I = index.search(
                    np.array([query_embedding]).astype("float32"),
                    15  # over-fetch for filtering
                )

                results = []
                for idx in I[0]:
                    if idx < 0 or idx >= len(metadata):
                        continue
                    meta = metadata[idx]
                    if (
                        meta.get("user_id") == uid and
                        meta.get("chat_session_id") == session_id
                    ):
                        results.append(meta)
                    if len(results) >= 5:
                        break

                return results
            except Exception:
                pass

        # Fallback to standard faiss service search
        return self.faiss.search(uid, session_id, query_embedding)

    def _format_memory(self, messages: list) -> str:
        """
        Format recent messages for prompt context.
        Messages are now plain text strings from Redis.
        """
        if not messages:
            return "No previous messages."

        # Messages are already plain text strings like "User: hello"
        return "\n".join(messages[-10:])  # Last 10 messages

    async def _generate_plain_response(self, prompt: str) -> str:
        """
        Generate a plain text response (not JSON).
        Uses a modified prompt to avoid JSON output.
        """
        try:
            # Try to get plain text response
            response = await self.llm.generate(prompt)
            
            # If response looks like JSON, extract the text
            if response.strip().startswith("{"):
                try:
                    data = json.loads(response)
                    # Try common text fields
                    for key in ["message", "response", "text", "answer", "content"]:
                        if key in data:
                            return str(data[key])
                    # Return first string value found
                    for value in data.values():
                        if isinstance(value, str) and len(value) > 10:
                            return value
                except json.JSONDecodeError:
                    pass
            
            return response.strip()
        except Exception as e:
            return f"I encountered an issue processing your request. Please try again."