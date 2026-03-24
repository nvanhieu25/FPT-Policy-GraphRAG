"""
app/api/routes/conversation.py

Conversation management endpoints:
  GET    /conversations          — list all (PostgreSQL)
  GET    /history/{session_id}   — message history (PostgreSQL)
  DELETE /history/{session_id}   — delete conversation + Redis cache
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.conversation import (
    HistoryResponse,
    DeleteResponse,
    MessageItem,
    ConversationSummary,
    ConversationsListResponse,
)
from app.services.cache_service import delete_chat_history
from app.services.conversation_service import (
    list_conversations,
    get_messages,
    delete_conversation,
)
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/conversations",
    response_model=ConversationsListResponse,
    summary="List all conversations",
)
async def get_conversations(db: AsyncSession = Depends(get_db)):
    convs = await list_conversations(db)
    return ConversationsListResponse(
        conversations=[
            ConversationSummary(
                id=c.id,
                title=c.title,
                message_count=c.message_count,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in convs
        ]
    )


@router.get(
    "/history/{session_id}",
    response_model=HistoryResponse,
    summary="Get conversation history",
)
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    msgs = await get_messages(db, session_id)
    if not msgs:
        return HistoryResponse(session_id=session_id, messages=[])
    return HistoryResponse(
        session_id=session_id,
        messages=[MessageItem(role=m.role, content=m.content) for m in msgs],
    )


@router.delete(
    "/history/{session_id}",
    response_model=DeleteResponse,
    summary="Delete a conversation",
)
async def delete_history(session_id: str, db: AsyncSession = Depends(get_db)):
    found = await delete_conversation(db, session_id)
    if not found:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        await delete_chat_history(session_id)
    except Exception:
        pass
    return DeleteResponse(session_id=session_id)
