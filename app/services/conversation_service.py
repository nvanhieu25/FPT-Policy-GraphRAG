"""
app/services/conversation_service.py

CRUD helpers for Conversation and Message persistence in PostgreSQL.
"""
import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Message


async def get_or_create_conversation(db: AsyncSession, session_id: str) -> Conversation:
    """Return existing conversation or create a new one."""
    result = await db.get(Conversation, session_id)
    if result:
        return result
    conv = Conversation(
        id=session_id,
        title="Cuộc trò chuyện mới",
        message_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def save_messages(
    db: AsyncSession,
    session_id: str,
    user_query: str,
    ai_answer: str,
) -> Conversation:
    """Save a user+AI message pair and update the conversation metadata."""
    conv = await get_or_create_conversation(db, session_id)

    # Set title from first user message
    if conv.title == "Cuộc trò chuyện mới":
        conv.title = user_query[:80] + ("…" if len(user_query) > 80 else "")

    now = datetime.utcnow()
    db.add(Message(id=str(uuid.uuid4()), conversation_id=session_id, role="human", content=user_query, created_at=now))
    db.add(Message(id=str(uuid.uuid4()), conversation_id=session_id, role="ai",    content=ai_answer,  created_at=now))

    conv.message_count += 2
    conv.updated_at = now

    await db.commit()
    await db.refresh(conv)
    return conv


async def list_conversations(db: AsyncSession) -> list[Conversation]:
    """Return all conversations ordered by last updated."""
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


async def get_messages(db: AsyncSession, session_id: str) -> list[Message]:
    """Return all messages for a conversation ordered by creation time."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == session_id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()


async def delete_conversation(db: AsyncSession, session_id: str) -> bool:
    """Delete a conversation and all its messages. Returns False if not found."""
    conv = await db.get(Conversation, session_id)
    if not conv:
        return False
    await db.delete(conv)
    await db.commit()
    return True
