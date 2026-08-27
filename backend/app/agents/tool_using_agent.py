"""
Tool-Using Agent — uses function-calling to interact with backend services.
Has access to backend "tools" like get_pet_profile, get_behavior_history, etc.
"""

import json
import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base import BaseAgent
from app.models.pet import Pet
from app.models.behavior_log import BehaviorLog
from app.models.vaccination import Vaccination
from app.models.notification import Notification, NotificationType
from app.core.config import settings

logger = logging.getLogger(__name__)


# Tool definitions for the agent
TOOLS = [
    {
        "name": "get_pet_profile",
        "description": "Get the full profile of a pet including name, species, breed, weight, age, and medical history",
        "input_schema": {
            "type": "object",
            "properties": {"pet_id": {"type": "string", "description": "The pet's ID"}},
            "required": ["pet_id"],
        },
    },
    {
        "name": "get_behavior_history",
        "description": "Get recent behavior logs for a pet",
        "input_schema": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "string"},
                "limit": {"type": "integer", "description": "Max entries to return", "default": 10},
            },
            "required": ["pet_id"],
        },
    },
    {
        "name": "get_upcoming_vaccinations",
        "description": "Get vaccinations that are due soon for a pet",
        "input_schema": {
            "type": "object",
            "properties": {"pet_id": {"type": "string"}},
            "required": ["pet_id"],
        },
    },
    {
        "name": "create_reminder",
        "description": "Create a notification reminder for the user about their pet",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The reminder message"},
            },
            "required": ["message"],
        },
    },
]


class ToolUsingAgent(BaseAgent):
    name = "tool_using_agent"
    description = "Uses function-calling to interact with backend services"

    async def run(
        self,
        message: str,
        user_id: str,
        pet_id: Optional[str],
        db: AsyncSession,
        **kwargs: Any,
    ) -> str:
        if settings.ANTHROPIC_API_KEY:
            try:
                return await self._run_with_tools(message, user_id, pet_id, db)
            except Exception as e:
                logger.error(f"Tool-using agent error: {e}")
                return await self._run_mock(message, user_id, pet_id, db)
        else:
            return await self._run_mock(message, user_id, pet_id, db)

    async def _run_with_tools(
        self, message: str, user_id: str, pet_id: Optional[str], db: AsyncSession
    ) -> str:
        """Run with Claude's tool-use capability."""
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        messages = [{"role": "user", "content": message}]

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=(
                "You are a pet care assistant with access to tools. "
                "Use the available tools to look up pet information and help the user. "
                f"Current pet_id: {pet_id or 'none selected'}, user_id: {user_id}"
            ),
            tools=TOOLS,
            messages=messages,
        )

        # Process tool calls
        while response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await self._execute_tool(
                        block.name, block.input, user_id, pet_id, db
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=(
                    "You are a pet care assistant with access to tools. "
                    f"Current pet_id: {pet_id or 'none selected'}, user_id: {user_id}"
                ),
                tools=TOOLS,
                messages=messages,
            )

        # Extract final text response
        text_parts = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(text_parts) if text_parts else "I've completed the requested action."

    async def _execute_tool(
        self, tool_name: str, args: dict, user_id: str, pet_id: Optional[str], db: AsyncSession
    ) -> dict:
        """Execute a tool function and return the result."""
        target_pet_id = args.get("pet_id", pet_id)

        if tool_name == "get_pet_profile":
            result = await db.execute(select(Pet).where(Pet.id == target_pet_id))
            pet = result.scalar_one_or_none()
            if pet:
                return {
                    "name": pet.name, "species": pet.species, "breed": pet.breed,
                    "dob": str(pet.dob), "weight": pet.weight, "gender": pet.gender,
                    "medical_history": pet.medical_history,
                }
            return {"error": "Pet not found"}

        elif tool_name == "get_behavior_history":
            limit = args.get("limit", 10)
            result = await db.execute(
                select(BehaviorLog)
                .where(BehaviorLog.pet_id == target_pet_id)
                .order_by(BehaviorLog.logged_at.desc())
                .limit(limit)
            )
            logs = result.scalars().all()
            return {"logs": [
                {"date": str(l.logged_at), "category": l.category,
                 "value": l.value, "anomaly": l.flagged_anomaly}
                for l in logs
            ]}

        elif tool_name == "get_upcoming_vaccinations":
            from datetime import date
            result = await db.execute(
                select(Vaccination)
                .where(Vaccination.pet_id == target_pet_id)
                .where(Vaccination.next_due_date >= date.today())
                .order_by(Vaccination.next_due_date)
            )
            vaxes = result.scalars().all()
            return {"vaccinations": [
                {"vaccine": v.vaccine_name, "next_due": str(v.next_due_date)}
                for v in vaxes
            ]}

        elif tool_name == "create_reminder":
            notif = Notification(
                user_id=user_id,
                pet_id=pet_id,
                type=NotificationType.SYSTEM,
                message=args["message"],
            )
            db.add(notif)
            await db.flush()
            return {"status": "reminder_created", "message": args["message"]}

        return {"error": f"Unknown tool: {tool_name}"}

    async def _run_mock(
        self, message: str, user_id: str, pet_id: Optional[str], db: AsyncSession
    ) -> str:
        """Mock tool execution for when no API key is available."""
        if pet_id:
            result = await db.execute(select(Pet).where(Pet.id == pet_id))
            pet = result.scalar_one_or_none()
            if pet:
                return (
                    f"🔧 **Tool Agent Report for {pet.name}:**\n\n"
                    f"• Species: {pet.species}\n"
                    f"• Breed: {pet.breed or 'Not specified'}\n"
                    f"• Weight: {pet.weight or 'Not recorded'} kg\n\n"
                    f"*Connect an ANTHROPIC_API_KEY for advanced tool-based interactions "
                    f"(auto-lookups, smart reminders, behavior analysis).*"
                )
        return "🔧 Please select a pet for me to look up information about."
