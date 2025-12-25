from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    @abstractmethod
    async def run(self, *args, **kwargs):
        """
        Execute the agent's main functionality.
        
        Must be implemented by subclasses.
        """
        pass
