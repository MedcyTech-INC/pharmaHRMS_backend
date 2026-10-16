from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class LeaveApplyRequest(BaseModel):
    employee_id: Optional[str] = None
    leave_type: str
    from_date: date
    to_date: date
    reason: Optional[str] = None

class LeaveActionRequest(BaseModel):
    admin_note: Optional[str] = None

class LeaveBalanceUpdate(BaseModel):
    leave_type: str
    total_allotted: int
    used: int

class LeaveResponse(BaseModel):
    id: UUID
    employee_id: str
    leave_type: str
    from_date: date
    to_date: date
    reason: Optional[str] = None
    status: str
    submitted_at: Optional[date] = None
    admin_note: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LeaveBalanceResponse(BaseModel):
    id: UUID
    employee_id: str
    leave_type: str
    total_allotted: int
    used: int

    class Config:
        from_attributes = True

class MonthlyQuotaResponse(BaseModel):
    id: UUID
    employee_id: str
    month: str
    allotted: int
    used: int
    remaining: int

    class Config:
        from_attributes = True
