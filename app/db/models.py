"""
app/db/models.py

SQLAlchemy ORM models for persistent conversation storage.
"""
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id               = Column(String(36), primary_key=True)
    email            = Column(String(255), unique=True, nullable=False, index=True)
    username         = Column(String(100), unique=True, nullable=False)
    hashed_password  = Column(String(255), nullable=False)
    is_active        = Column(Boolean, default=True, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)
    conversations    = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id           = Column(String(36), primary_key=True)
    title        = Column(String(255), default="Cuộc trò chuyện mới", nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user    = relationship("User", back_populates="conversations")

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id              = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role            = Column(String(10), nullable=False)   # "human" | "ai"
    content         = Column(Text, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
