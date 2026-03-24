"""
app/services/cache_service.py

Handles conversation history storage in Redis using pickle serialization.
Provides async functions for reading and writing LangChain message histories.
"""
import pickle
import logging
from typing import TYPE_CHECKING

from app.core.redis_client import get_redis_client

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

# TTL for conversation sessions: 24 hours
SESSION_TTL_SECONDS = 60 * 60 * 24


def _session_key(session_id: str) -> str:
    return f"chat:history:{session_id}"


async def get_chat_history(session_id: str) -> list["BaseMessage"]:
    """Retrieve the conversation history for a session from Redis.

    Returns an empty list if the session does not exist or has expired.
    """
    client = get_redis_client()
    try:
        raw = await client.get(_session_key(session_id))
        if raw is None:
            return []
        messages = pickle.loads(raw)  # noqa: S301
        logger.debug("[Cache] Loaded %d messages for session '%s'.", len(messages), session_id)
        return messages
    except Exception as e:
        logger.warning("[Cache] Failed to load history for session '%s': %s", session_id, e)
        return []
    finally:
        await client.aclose()


async def update_chat_history(session_id: str, messages: list["BaseMessage"]) -> None:
    """Persist (overwrite) the full conversation history for a session in Redis.

    The session will automatically expire after SESSION_TTL_SECONDS.
    """
    client = get_redis_client()
    try:
        raw = pickle.dumps(messages)
        await client.set(_session_key(session_id), raw, ex=SESSION_TTL_SECONDS)
        logger.debug("[Cache] Saved %d messages for session '%s'.", len(messages), session_id)
    except Exception as e:
        logger.warning("[Cache] Failed to save history for session '%s': %s", session_id, e)
    finally:
        await client.aclose()


async def delete_chat_history(session_id: str) -> None:
    """Delete the conversation history for a session (e.g., on logout / reset)."""
    client = get_redis_client()
    try:
        await client.delete(_session_key(session_id))
        logger.debug("[Cache] Deleted history for session '%s'.", session_id)
    except Exception as e:
        logger.warning("[Cache] Failed to delete history for session '%s': %s", session_id, e)
    finally:
        await client.aclose()
