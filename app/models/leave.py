from sqlalchemy import Column, String, Date, Integer, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class LeaveRequest(Base):
    __tablename__ = "pharma_hrms_leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    leave_type = Column(String(100), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(String(50), nullable=False, default="pending")
    submitted_at = Column(Date, server_default=func.current_date())
    admin_note = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class LeaveBalance(Base):
    __tablename__ = "pharma_hrms_leave_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    leave_type = Column(String(100), nullable=False)
    total_allotted = Column(Integer, nullable=False, default=0)
    used = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class MonthlyLeaveQuota(Base):
    __tablename__ = "pharma_hrms_monthly_leave_quota"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    month = Column(String(7), nullable=False)  # 'YYYY-MM'
    allotted = Column(Integer, nullable=False, default=3)
    used = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
