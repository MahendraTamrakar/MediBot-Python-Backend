class EmbeddingService:
    def __init__(self, llm):
        self.llm = llm

    async def embed(self, text: str) -> list[float]:
        return await self.llm.embed(text)