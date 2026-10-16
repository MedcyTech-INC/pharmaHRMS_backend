from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class TaskCreate(BaseModel):
    title: Optional[str] = None
    description: str
    priority: Optional[str] = "medium"
    due_date: Optional[date] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

class TaskStatusUpdate(BaseModel):
    status: str

class TaskApprovalRequest(BaseModel):
    action: str  # 'approve' | 'reject'
    note: Optional[str] = None

class TaskResponse(BaseModel):
    id: UUID
    title: Optional[str] = None
    description: str
    priority: str
    status: str
    due_date: Optional[date] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    approval_status: Optional[str] = "not_required"
    approval_note: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: UUID
    recipient_id: str
    sender_id: Optional[str] = None
    title: str
    message: str
    type: str
    is_read: bool
    reference_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
