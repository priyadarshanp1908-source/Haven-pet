"""Base agent — abstract interface for all Haven Pet AI agents."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.
    Each agent has a single `run()` entrypoint, making them
    independently testable and composable by the orchestrator.
    """

    name: str = "base_agent"
    description: str = "Base agent interface"

    @abstractmethod
    async def run(
        self,
        message: str,
        user_id: str,
        pet_id: Optional[str],
        db: AsyncSession,
        **kwargs: Any,
    ) -> str:
        """
        Process a request and return a response string.

        Args:
            message: The user's input message or instruction
            user_id: ID of the requesting user
            pet_id: Optional pet ID for context
            db: Async database session
            **kwargs: Additional context (e.g., conversation history)

        Returns:
            Response string from the agent
        """
        ...
