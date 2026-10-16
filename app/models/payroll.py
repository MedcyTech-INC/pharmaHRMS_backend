from sqlalchemy import Column, String, Numeric, Integer, Boolean, JSON, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class PayrollRecord(Base):
    __tablename__ = "pharma_hrms_payroll"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    month = Column(String(7), nullable=False)
    basic_pay = Column(Numeric(12, 2), nullable=False, default=0.00)
    allowances = Column(JSON, default=list)
    deductions = Column(JSON, default=list)
    net_pay = Column(Numeric(12, 2), nullable=False, default=0.00)
    advance_money_taken = Column(Boolean, default=False)
    advance_money_amount = Column(Numeric(12, 2), default=0.00)
    working_days = Column(Integer)
    days_present = Column(Integer)
    leaves_taken = Column(Integer)
    is_finalized = Column(Boolean, default=False)
    finalized_by = Column(String(255))
    finalized_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class AdvanceRequest(Base):
    __tablename__ = "pharma_hrms_advance_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text)
    status = Column(String(50), nullable=False, default="pending")
    repayment_months = Column(Integer, default=2)
    monthly_installment = Column(Numeric(12, 2), default=0.00)
    installments_remaining = Column(Integer, default=2)
    advance_type = Column(String(50), default="salary")
    approved_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class PayrollConfig(Base):
    __tablename__ = "pharma_hrms_payroll_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Numeric(12, 2), default=0.00)
    label = Column(Text)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
