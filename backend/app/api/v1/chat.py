"""Chat routes — AI chatbot endpoint routed through the agent orchestrator."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.user import User
from app.models.chat_message import ChatMessage, ChatRole
from app.agents.orchestrator import orchestrator

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the AI chatbot.
    Routes through the orchestrator which picks the best sub-agent.
    """
    # Persist user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        pet_id=data.pet_id,
        role=ChatRole.USER,
        content=data.message,
    )
    db.add(user_msg)
    await db.flush()

    # Run through orchestrator
    agent_name = orchestrator.get_agent_name(data.message)
    reply = await orchestrator.run(
        message=data.message,
        user_id=current_user.id,
        pet_id=data.pet_id,
        db=db,
    )

    # Persist assistant response
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        pet_id=data.pet_id,
        role=ChatRole.ASSISTANT,
        content=reply,
    )
    db.add(assistant_msg)
    await db.flush()

    return ChatResponse(reply=reply, agent_used=agent_name)
