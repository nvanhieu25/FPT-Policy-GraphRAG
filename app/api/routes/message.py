"""
app/api/routes/message.py

POST /chat — runs the GraphRAG pipeline, persists to Redis (AI context)
and PostgreSQL (display / history).
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage

from app.schemas.conversation import ChatRequest, ChatResponse
from app.services.ai_service import run_query
from app.services.cache_service import get_chat_history, update_chat_history
from app.services.conversation_service import save_messages
from app.db.session import get_db
from app.core.auth import get_current_user
from app.db.models import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, summary="Send a message to the compliance assistant")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    session_id = request.session_id
    query      = request.query

    logger.info("[/chat] user=%s session=%s | query='%s'", current_user.id, session_id, query[:80])

    # 1. Load existing history from Redis (LangChain context)
    history = await get_chat_history(session_id)

    # 2. Run GraphRAG pipeline (with RAG cache)
    try:
        answer = await run_query(question=query, history=history)
    except Exception as e:
        logger.error("[/chat] Pipeline error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}") from e

    # 3. Persist to Redis
    history.append(HumanMessage(content=query))
    history.append(AIMessage(content=answer))
    await update_chat_history(session_id, history)

    # 4. Persist to PostgreSQL
    await save_messages(db, session_id, query, answer, user_id=current_user.id)

    logger.info("[/chat] session=%s | answer generated (%d chars)", session_id, len(answer))
    return ChatResponse(session_id=session_id, answer=answer)
