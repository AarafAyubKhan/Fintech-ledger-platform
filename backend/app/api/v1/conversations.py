"""
FinSight AI — Conversation Endpoints
Chat interface with streaming agent responses via WebSocket.
"""

import time
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select, func
from uuid6 import uuid7

from app.api.deps import CurrentUser, DBSession
from app.core.exceptions import NotFoundException
from app.models.conversation import Conversation, ConversationStatus, Message, MessageRole
from app.schemas import (
    ConversationDetailResponse,
    ConversationResponse,
    CreateConversationRequest,
    MessageRequest,
    MessageResponse,
)

router = APIRouter()
logger = structlog.get_logger()


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    user: CurrentUser,
    db: DBSession,
) -> ConversationResponse:
    """Create a new conversation."""
    conversation = Conversation(
        id=str(uuid7()),
        user_id=user.id,
        title=request.title or "New Research Query",
        status=ConversationStatus.ACTIVE,
    )
    db.add(conversation)
    await db.flush()
    return ConversationResponse.model_validate(conversation)


@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(
    user: CurrentUser,
    db: DBSession,
    skip: int = 0,
    limit: int = 50,
) -> list[ConversationResponse]:
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    conversations = result.scalars().all()
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    user: CurrentUser,
    db: DBSession,
) -> ConversationDetailResponse:
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundException("Conversation", conversation_id)

    # Get messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    return ConversationDetailResponse(
        conversation=ConversationResponse.model_validate(conversation),
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.post("/{conversation_id}/message", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: MessageRequest,
    user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    """Send a message and get an AI-powered response with citations."""
    # Verify conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundException("Conversation", conversation_id)

    start_time = time.perf_counter()

    # Save user message
    user_message = Message(
        id=str(uuid7()),
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.content,
    )
    db.add(user_message)

    # Run agent pipeline
    from app.agents.orchestrator import run_agent_pipeline

    try:
        conversation.status = ConversationStatus.PROCESSING
        agent_result = await run_agent_pipeline(
            query=request.content,
            conversation_id=conversation_id,
            user_id=user.id,
            db=db,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Save assistant response
        assistant_message = Message(
            id=str(uuid7()),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=agent_result.get("answer", "I was unable to generate a response."),
            citations=agent_result.get("citations"),
            sources=agent_result.get("sources"),
            execution_steps=agent_result.get("execution_steps"),
            agent_name=agent_result.get("final_agent", "orchestrator"),
            latency_ms=latency_ms,
            token_count=agent_result.get("total_tokens"),
        )
        db.add(assistant_message)

        # Update conversation stats
        conversation.message_count += 2
        conversation.total_tokens += agent_result.get("total_tokens", 0)
        conversation.status = ConversationStatus.ACTIVE
        conversation.agent_state = agent_result.get("state_snapshot")

        await db.flush()

        logger.info(
            "message_processed",
            conversation_id=conversation_id,
            latency_ms=latency_ms,
        )

        return MessageResponse.model_validate(assistant_message)

    except Exception as e:
        conversation.status = ConversationStatus.FAILED
        error_message = Message(
            id=str(uuid7()),
            conversation_id=conversation_id,
            role=MessageRole.SYSTEM,
            content=f"An error occurred while processing your request: {str(e)}",
        )
        db.add(error_message)
        await db.flush()

        logger.error("message_processing_failed", error=str(e))
        return MessageResponse.model_validate(error_message)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundException("Conversation", conversation_id)

    await db.delete(conversation)
