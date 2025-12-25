from abc import ABC, abstractmethod

class LLMInterface(ABC):
    @abstractmethod
    async def stream_response(self, prompt: str):
        pass