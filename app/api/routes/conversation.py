"""
app/api/routes/conversation.py

Conversation management endpoints:
  GET    /conversations          — list user's conversations (PostgreSQL)
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
    get_conversation,
)
from app.db.session import get_db
from app.core.auth import get_current_user
from app.db.models import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/conversations",
    response_model=ConversationsListResponse,
    summary="List all conversations for current user",
)
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convs = await list_conversations(db, user_id=current_user.id)
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
async def get_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await get_conversation(db, session_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = await get_messages(db, session_id)
    return HistoryResponse(
        session_id=session_id,
        messages=[MessageItem(role=m.role, content=m.content) for m in msgs],
    )


@router.delete(
    "/history/{session_id}",
    response_model=DeleteResponse,
    summary="Delete a conversation",
)
async def delete_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await get_conversation(db, session_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    found = await delete_conversation(db, session_id)
    if not found:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        await delete_chat_history(session_id)
    except Exception:
        pass
    return DeleteResponse(session_id=session_id)
