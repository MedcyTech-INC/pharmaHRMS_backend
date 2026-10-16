from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID

class PayrollTier(BaseModel):
    id: str
    name: str
    minSalary: Decimal
    maxSalary: Decimal
    hra: Decimal
    ma: Decimal
    ca: Decimal

class PayrollConfigRequest(BaseModel):
    payroll_tiers: Optional[List[PayrollTier]] = None
    pf_percent: Optional[Decimal] = Decimal("12.0")
    professional_tax: Optional[Decimal] = Decimal("200.0")

class SavePayslipRequest(BaseModel):
    employee_id: str
    month: str
    basic_pay: Decimal
    allowances: List[Dict[str, Any]]
    deductions: List[Dict[str, Any]]
    net_pay: Optional[Decimal] = None
    advance_money_taken: Optional[bool] = False
    advance_money_amount: Optional[Decimal] = Decimal("0.00")
    working_days: Optional[int] = None
    days_present: Optional[int] = None
    leaves_taken: Optional[int] = None

class BulkPayrollRequest(BaseModel):
    month: str
    employee_ids: Optional[List[str]] = None

class AdvanceApplyRequest(BaseModel):
    employee_id: Optional[str] = None
    amount: Decimal
    reason: str
    repayment_months: int = 2
    advance_type: str = "salary"

class AdvanceActionRequest(BaseModel):
    admin_note: Optional[str] = None

class FinalizePeriodRequest(BaseModel):
    month: str
    admin_note: Optional[str] = None

class PayrollResponse(BaseModel):
    id: UUID
    employee_id: str
    month: str
    basic_pay: Decimal
    allowances: List[Dict[str, Any]]
    deductions: List[Dict[str, Any]]
    net_pay: Decimal
    advance_money_taken: bool
    advance_money_amount: Decimal
    working_days: Optional[int] = None
    days_present: Optional[int] = None
    leaves_taken: Optional[int] = None
    is_finalized: Optional[bool] = False
    finalized_by: Optional[str] = None
    finalized_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdvanceResponse(BaseModel):
    id: UUID
    employee_id: str
    amount: Decimal
    reason: Optional[str] = None
    status: str
    repayment_months: int
    monthly_installment: Decimal
    installments_remaining: int
    advance_type: str
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
