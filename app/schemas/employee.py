from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal

class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "employee"
    designation: str
    employee_code: Optional[str] = None
    joining_date: Optional[date] = None
    basic_pay: Decimal = Decimal("0.00")
    status: str = "active"
    phone: Optional[str] = None
    gender: Optional[str] = "male"
    experience: Optional[Decimal] = Decimal("0.0")
    dob: Optional[date] = None
    hospital: Optional[str] = "orca_labs"
    branch: Optional[str] = "corporate"
    hierarchy_level: str = "be"
    zone: Optional[str] = "AP"
    territory: Optional[str] = None
    reporting_to: Optional[str] = None
    cl_balance: Optional[int] = 12
    pl_balance: Optional[int] = 4
    bank_details: Optional[Dict[str, Any]] = None

class EmployeeCreate(EmployeeBase):
    id: str
    password: str

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    basic_pay: Optional[Decimal] = None
    status: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    experience: Optional[Decimal] = None
    dob: Optional[date] = None
    hospital: Optional[str] = None
    branch: Optional[str] = None
    hierarchy_level: Optional[str] = None
    zone: Optional[str] = None
    territory: Optional[str] = None
    reporting_to: Optional[str] = None
    cl_balance: Optional[int] = None
    pl_balance: Optional[int] = None
    bank_details: Optional[Dict[str, Any]] = None

class ChangePasswordRequest(BaseModel):
    new_password: str

class EmployeePublicResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str = "employee"
    designation: str
    employee_code: Optional[str] = None
    status: str = "active"
    phone: Optional[str] = None
    gender: Optional[str] = "male"
    experience: Optional[Decimal] = Decimal("0.0")
    hospital: Optional[str] = "orca_labs"
    branch: Optional[str] = "corporate"
    hierarchy_level: str = "be"
    zone: Optional[str] = "AP"
    territory: Optional[str] = None
    reporting_to: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmployeeAdminResponse(EmployeePublicResponse):
    joining_date: Optional[date] = None
    dob: Optional[date] = None
    basic_pay: Decimal = Decimal("0.00")
    cl_balance: Optional[int] = 12
    pl_balance: Optional[int] = 4
    bank_details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Standard response alias (defaults to admin model for types)
EmployeeResponse = EmployeeAdminResponse
