from sqlalchemy import Column, String, Date, Text, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class Task(Base):
    __tablename__ = "pharma_hrms_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="in_progress")
    due_date = Column(Date, server_default=func.current_date())
    assigned_to = Column(String(255))
    created_by = Column(String(255))
    notes = Column(Text)
    completed_at = Column(TIMESTAMP(timezone=True))
    approval_status = Column(String(20), default="not_required")
    approval_note = Column(Text)
    approved_by = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class Notification(Base):
    __tablename__ = "pharma_hrms_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id = Column(String(255), nullable=False)
    sender_id = Column(String(255))
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, default="general")
    is_read = Column(Boolean, nullable=False, default=False)
    reference_id = Column(UUID(as_uuid=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
