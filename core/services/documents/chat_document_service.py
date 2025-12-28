import uuid

class ChatDocumentService:
    def __init__(self, vector_store, embedder):
        self.vector_store = vector_store
        self.embedder = embedder

    async def ingest_document(
        self,
        user_id: str,
        chat_session_id: str,
        text: str
    ) -> str:
        document_id = str(uuid.uuid4())
        chunks = self._chunk(text)

        vectors = []
        metadata = []

        for i, chunk in enumerate(chunks):
            vec = await self.embedder.embed(chunk)
            vectors.append(vec)
            metadata.append({
                "user_id": user_id,
                "chat_session_id": chat_session_id,
                "document_id": document_id,
                "chunk_id": i,
                "text": chunk
            })

        self.vector_store.add(vectors, metadata)
        return document_id

    def _chunk(self, text, size=500, overlap=50):
        chunks = []
        i = 0
        while i < len(text):
            chunks.append(text[i:i+size])
            i += size - overlap
        return chunks