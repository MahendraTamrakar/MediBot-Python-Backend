from abc import ABC, abstractmethod

class SafetyInterface(ABC):
    @abstractmethod
    def is_allowed(self, text: str) -> bool:
        pass

    @abstractmethod
    def disclaimer(self) -> str:
        pass