import json
from prompts.medical_prompt import build_medical_prompt


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
        Unified chat pipeline with document-QA priority (non-streaming).
        
        If documents exist for the session → always use document-QA mode.
        Otherwise → use medical chat mode.
        """

        # Save user message
        await self.chat_history.save_message(
            firebase_uid=firebase_uid,
            session_id=session_id,
            role="user",
            content=message
        )

        # Emergency override (applies to both modes)
        if self.emergency.is_emergency(message):
            return await self._handle_emergency(firebase_uid, session_id)

        # Check if documents exist for this session
        has_documents = self.faiss.has_documents(firebase_uid, session_id)

        if has_documents:
            return await self._handle_document_chat(
                firebase_uid, session_id, message
            )
        else:
            return await self._handle_medical_chat(
                firebase_uid, session_id, message
            )

    async def stream_analyze(
        self,
        firebase_uid: str,
        session_id: str,
        message: str
    ):
        """
        Streaming chat pipeline with document-QA priority.
        Yields text tokens as they arrive from Gemini.
        
        Yields text chunks for streaming. Caller is responsible for 
        saving to history after stream completes.
        """

        # Save user message
        await self.chat_history.save_message(
            firebase_uid=firebase_uid,
            session_id=session_id,
            role="user",
            content=message
        )

        # Emergency override (applies to both modes)
        if self.emergency.is_emergency(message):
            response_text = (
                "⚠️ Your symptoms may require urgent medical attention. "
                "Please seek immediate medical care or call emergency services. "
                "Do not self-medicate. Avoid exertion until evaluated by a professional."
            )
            yield response_text
            return

        # Check if documents exist for this session
        has_documents = self.faiss.has_documents(firebase_uid, session_id)

        if has_documents:
            async for chunk in self._stream_document_chat(
                firebase_uid, session_id, message
            ):
                yield chunk
        else:
            async for chunk in self._stream_medical_chat(
                firebase_uid, session_id, message
            ):
                yield chunk

    async def _handle_emergency(self, firebase_uid: str, session_id: str) -> dict:
        """Handle emergency situations with immediate response."""
        message = (
            "⚠️ Your symptoms may require urgent medical attention. "
            "Please seek immediate medical care or call emergency services. "
            "Do not self-medicate. Avoid exertion until evaluated by a professional."
        )

        await self.chat_history.save_message(
            firebase_uid, session_id, "assistant", message
        )

        return {
            "type": "medical_chat",
            "message": message
        }

    async def _handle_document_chat(
        self,
        firebase_uid: str,
        session_id: str,
        message: str
    ) -> dict:
        """
        Document-QA mode: Answer questions from uploaded documents.
        Returns plain chat-style text (no structured medical format).
        """
        # Get conversation context
        recent_memory = await self.redis.get_recent_messages(firebase_uid, session_id)
        memory_text = self._format_memory(recent_memory)

        # Search for relevant document chunks
        query_embedding = await self.embedder.embed(message)
        faiss_results = self._search_document_store(firebase_uid, session_id, query_embedding)

        # Build document context (may be empty)
        document_context = ""
        if faiss_results:
            document_context = "\n\n".join(
                chunk["text"] if isinstance(chunk, dict) else str(chunk)
                for chunk in faiss_results[:5]
            )

        # Build document-QA prompt
        if document_context:
            prompt = f"""
You are a helpful assistant answering questions about an uploaded document.

Answer the user's question using ONLY the document context below.
Be concise and direct. Do not add medical disclaimers unless specifically relevant.

Document context:
{document_context}

Recent conversation:
{memory_text}

User question:
{message}

Provide a natural, conversational response.
"""
        else:
            # Documents exist but no relevant chunks found
            prompt = f"""
The user has uploaded a document to this chat session, but I could not find 
relevant information matching their question.

User question: {message}

Recent conversation:
{memory_text}

Respond helpfully, letting them know you couldn't find this specific information 
in the uploaded document. Suggest they rephrase or ask about different aspects of the document.
"""

        # Generate response (plain text, not JSON)
        response_text = await self._generate_plain_response(prompt)

        # Save to history
        await self.chat_history.save_message(
            firebase_uid, session_id, "assistant", response_text
        )
        await self.redis.save_message(
            firebase_uid, session_id, "assistant", response_text
        )

        return {
            "type": "document_chat",
            "message": response_text
        }

    async def _handle_medical_chat(
        self,
        firebase_uid: str,
        session_id: str,
        message: str
    ) -> dict:
        """
        Medical chat mode: Plain text symptom analysis.
        Returns simple chat-style message (no structured cards).
        """
        # Get context
        profile_context = await self.context_service.build_context(firebase_uid)
        recent_memory = await self.redis.get_recent_messages(firebase_uid, session_id)
        memory_text = self._format_memory(recent_memory)

        # Build medical prompt (plain text, safety-focused)
        context = f"User profile:\n{profile_context}\n\nRecent conversation:\n{memory_text}"
        prompt = build_medical_prompt(
            user_input=message,
            context=context
        )

        # Generate plain text response
        response_text = await self._generate_plain_response(prompt)

        # Save to history
        await self.chat_history.save_message(
            firebase_uid, session_id, "assistant", response_text
        )
        await self.redis.save_message(
            firebase_uid, session_id, "assistant", response_text
        )

        return {
            "type": "medical_chat",
            "message": response_text
        }

        return data

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
        """Format recent messages for prompt context."""
        if not messages:
            return "No previous messages."

        formatted = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                formatted.append(f"{role.capitalize()}: {content}")
            else:
                formatted.append(str(msg))

        return "\n".join(formatted[-6:])  # Last 6 messages

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

    async def _stream_document_chat(
        self,
        firebase_uid: str,
        session_id: str,
        message: str
    ):
        """
        Stream document-QA responses. Yields text chunks and returns full response.
        """
        # Get conversation context
        recent_memory = await self.redis.get_recent_messages(firebase_uid, session_id)
        memory_text = self._format_memory(recent_memory)

        # Search for relevant document chunks
        query_embedding = await self.embedder.embed(message)
        faiss_results = self._search_document_store(firebase_uid, session_id, query_embedding)

        # Build document context (may be empty)
        document_context = ""
        if faiss_results:
            document_context = "\\n\\n".join(
                chunk["text"] if isinstance(chunk, dict) else str(chunk)
                for chunk in faiss_results[:5]
            )

        # Build document-QA prompt
        if document_context:
            prompt = f"""
You are a helpful assistant answering questions about an uploaded document.

Answer the user's question using ONLY the document context below.
Be concise and direct. Do not add medical disclaimers unless specifically relevant.

Document context:
{document_context}

Recent conversation:
{memory_text}

User question:
{message}

Provide a natural, conversational response.
"""
        else:
            # Documents exist but no relevant chunks found
            prompt = f"""
The user has uploaded a document to this chat session, but I could not find 
relevant information matching their question.

User question: {message}

Recent conversation:
{memory_text}

Respond helpfully, letting them know you couldn't find this specific information 
in the uploaded document. Suggest they rephrase or ask about different aspects of the document.
"""

        # Stream response
        full_response = ""
        async for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield chunk

        # Caller is responsible for saving to history after stream completes

    async def _stream_medical_chat(
        self,
        firebase_uid: str,
        session_id: str,
        message: str
    ):
        """
        Stream medical chat responses. Yields text chunks and returns full response.
        """
        # Get context
        profile_context = await self.context_service.build_context(firebase_uid)
        recent_memory = await self.redis.get_recent_messages(firebase_uid, session_id)
        memory_text = self._format_memory(recent_memory)

        # Build medical prompt (plain text, safety-focused)
        context = f"User profile:\n{profile_context}\n\nRecent conversation:\n{memory_text}"
        prompt = build_medical_prompt(
            user_input=message,
            context=context
        )

        # Stream response
        full_response = ""
        async for chunk in self.llm.stream(prompt):
            full_response += chunk
            yield chunk

        # Caller is responsible for saving to history after stream completes