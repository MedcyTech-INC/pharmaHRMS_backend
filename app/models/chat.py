from sqlalchemy import Column, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class ChatChannel(Base):
    __tablename__ = "pharma_hrms_chat_channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    type = Column(String(50), default="direct")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class ChatMessage(Base):
    __tablename__ = "pharma_hrms_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id = Column(UUID(as_uuid=True), nullable=False)
    sender_id = Column(String(255), nullable=False)
    text = Column(Text)
    attachment_url = Column(String(255))
    attachment_type = Column(String(50))
    attachment_name = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class MessageRead(Base):
    __tablename__ = "pharma_hrms_message_reads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(String(255), nullable=False)
    read_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
