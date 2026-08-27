"""
Intelligent Pet Care Agent (Orchestrator) — receives user requests,
classifies intent, routes to the appropriate sub-agent, and composes the final response.
"""

import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.agents.conversational_agent import ConversationalAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.tool_using_agent import ToolUsingAgent

logger = logging.getLogger(__name__)


class Orchestrator(BaseAgent):
    name = "orchestrator"
    description = "Routes requests to the appropriate sub-agent"

    def __init__(self):
        self.conversational = ConversationalAgent()
        self.recommendation = RecommendationAgent()
        self.tool_using = ToolUsingAgent()

    async def run(
        self,
        message: str,
        user_id: str,
        pet_id: Optional[str],
        db: AsyncSession,
        **kwargs: Any,
    ) -> str:
        """Classify intent and route to the right sub-agent."""
        intent = self._classify_intent(message)
        logger.info(f"Orchestrator classified intent: {intent}")

        if intent == "recommendation":
            return await self.recommendation.run(message, user_id, pet_id, db, **kwargs)
        elif intent == "tool_action":
            return await self.tool_using.run(message, user_id, pet_id, db, **kwargs)
        elif intent == "health_assessment":
            # Route to conversational agent with health assessment flag
            return await self.conversational.run(
                message, user_id, pet_id, db, is_health_assessment=True, **kwargs
            )
        else:
            # Default to conversational agent
            return await self.conversational.run(message, user_id, pet_id, db, **kwargs)

    def _classify_intent(self, message: str) -> str:
        """
        Simple keyword-based intent classification.
        In production, this could be an LLM classifier or fine-tuned model.
        """
        msg_lower = message.lower()

        # Health / Symptom assessment keywords (check first — higher priority)
        health_keywords = [
            "sick", "symptom", "vomit", "vomiting", "lethargy", "lethargic",
            "not eating", "won't eat", "diarrhea", "limping", "swollen",
            "swelling", "discharge", "cough", "coughing", "sneeze", "sneezing",
            "rash", "bleeding", "lump", "bump", "itching", "scratching",
            "losing weight", "breathing", "panting", "wheezing", "shaking",
            "trembling", "health check", "symptom check", "is my pet sick",
            "what's wrong", "not feeling well", "acting strange", "acting weird",
        ]
        if any(kw in msg_lower for kw in health_keywords):
            return "health_assessment"

        # Recommendation keywords
        recommendation_keywords = [
            "recommend", "suggestion", "advice", "what should",
            "diet plan", "exercise plan", "enrichment", "personalized",
            "best food", "how much exercise", "improve",
        ]
        if any(kw in msg_lower for kw in recommendation_keywords):
            return "recommendation"

        # Tool action keywords (looking up data, creating reminders)
        tool_keywords = [
            "look up", "check", "find", "schedule", "set reminder",
            "create reminder", "when is", "upcoming", "vaccination due",
            "medication schedule", "show me", "what are",
        ]
        if any(kw in msg_lower for kw in tool_keywords):
            return "tool_action"

        # Default: conversation
        return "conversation"

    def get_agent_name(self, message: str) -> str:
        """Return the name of the agent that will handle this message."""
        intent = self._classify_intent(message)
        if intent == "recommendation":
            return self.recommendation.name
        elif intent == "tool_action":
            return self.tool_using.name
        elif intent == "health_assessment":
            return "health_assessment"
        return self.conversational.name


# Singleton orchestrator instance
orchestrator = Orchestrator()

