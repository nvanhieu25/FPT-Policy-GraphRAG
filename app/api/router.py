"""
app/api/router.py

Central APIRouter that aggregates all sub-routers.
Import this single router in main.py.
"""
from fastapi import APIRouter

from app.api.routes import auth, message, conversation

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(message.router, tags=["Chat"])
api_router.include_router(conversation.router, tags=["History"])
