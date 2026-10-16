from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime
from decimal import Decimal
from uuid import UUID

class FieldSessionStart(BaseModel):
    employee_id: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class FieldSessionEnd(BaseModel):
    session_id: UUID
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class FieldVisitCreate(BaseModel):
    employee_id: Optional[str] = None
    visit_type: str = "DOCTOR_VISIT"
    category: str = "doctor"
    title: str
    description: Optional[str] = None
    scheduled_date: date
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    assigned_latitude: Optional[Decimal] = None
    assigned_longitude: Optional[Decimal] = None
    assigned_address: Optional[str] = None
    allowed_radius_meters: Optional[int] = 300
    priority: Optional[str] = "normal"
    doctor_name: Optional[str] = None
    clinic_name: Optional[str] = None
    area: Optional[str] = None
    time_slot: Optional[str] = None
    visit_purpose: Optional[str] = None

class FieldVisitComplete(BaseModel):
    actual_latitude: Optional[Decimal] = None
    actual_longitude: Optional[Decimal] = None
    actual_address: Optional[str] = None
    arrival_distance_m: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    proof_photo_url: Optional[str] = None
    completion_notes: Optional[str] = None
    products_detailed: Optional[List[Dict[str, Any]]] = None
    samples_given: Optional[List[Dict[str, Any]]] = None
    pob_amount: Optional[Decimal] = Decimal("0.00")

class LocationPinCreate(BaseModel):
    employee_id: Optional[str] = None
    visit_id: Optional[UUID] = None
    pin_type: str = "doctor_visit"
    label: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = "Other"
    description: Optional[str] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Decimal
    longitude: Decimal
    address: Optional[str] = None

class DoctorSubmissionCreate(BaseModel):
    employee_id: Optional[str] = None
    doctor_name: str
    specialization: Optional[str] = None
    clinic_hospital_name: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_time: Optional[str] = None
    potential: Optional[str] = "medium"
    notes: Optional[str] = None

class FieldVisitResponse(BaseModel):
    id: UUID
    session_id: Optional[UUID] = None
    employee_id: str
    assigned_by: Optional[str] = None
    visit_type: str
    category: str
    title: str
    description: Optional[str] = None
    scheduled_date: date
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    assigned_latitude: Optional[Decimal] = None
    assigned_longitude: Optional[Decimal] = None
    assigned_address: Optional[str] = None
    allowed_radius_meters: Optional[int] = 300
    priority: Optional[str] = "normal"
    status: str
    started_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_latitude: Optional[Decimal] = None
    actual_longitude: Optional[Decimal] = None
    actual_address: Optional[str] = None
    arrival_distance_m: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    proof_photo_url: Optional[str] = None
    completion_notes: Optional[str] = None
    location_exception: Optional[bool] = False
    approval_status: Optional[str] = "approved"
    doctor_name: Optional[str] = None
    clinic_name: Optional[str] = None
    area: Optional[str] = None
    time_slot: Optional[str] = None
    visit_purpose: Optional[str] = None
    products_detailed: Optional[List[Dict[str, Any]]] = None
    samples_given: Optional[List[Dict[str, Any]]] = None
    pob_amount: Optional[Decimal] = Decimal("0.00")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LocationPinResponse(BaseModel):
    id: UUID
    employee_id: str
    visit_id: Optional[UUID] = None
    date: date
    pinned_at: Optional[time] = None
    title: Optional[str] = None
    label: Optional[str] = None
    category: Optional[str] = "Other"
    description: Optional[str] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None
    location_name: Optional[str] = None
    pin_type: Optional[str] = "doctor_visit"
    latitude: Decimal
    longitude: Decimal
    address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
