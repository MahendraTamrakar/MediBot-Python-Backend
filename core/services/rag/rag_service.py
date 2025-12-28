class RAGService:
    def __init__(self, vector_store, embedder, llm):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm = llm

    async def answer(
        self,
        user_id: str,
        chat_session_id: str,
        question: str,
        chat_context: str
    ):
        q_vec = await self.embedder.embed(question)

        matches = self.vector_store.search(
            vector=q_vec,
            user_id=user_id,
            chat_session_id=chat_session_id
        )

        document_context = "\n".join(m["text"] for m in matches)

        prompt = f"""
You are a medical information assistant.

Document excerpts (may be from multiple documents):
{document_context}

Conversation context:
{chat_context}

User question:
{question}

Rules:
- Use ONLY the document excerpts when answering document-related questions
- If documents are insufficient, say so clearly
- Do NOT diagnose
- Add disclaimer
"""

        return await self.llm.generate(prompt) 