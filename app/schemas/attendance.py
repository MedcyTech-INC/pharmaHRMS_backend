from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime
from uuid import UUID

class ClockInRequest(BaseModel):
    employee_id: Optional[str] = None
    location: Optional[str] = None
    lat_lng: Optional[str] = None
    photo_url: Optional[str] = None
    punch_type: str = "in_office"
    punch_note: Optional[str] = None

class ClockOutRequest(BaseModel):
    employee_id: Optional[str] = None
    photo_url: Optional[str] = None
    location: Optional[str] = None
    lat_lng: Optional[str] = None

class ForceCloseRequest(BaseModel):
    employee_id: str
    date: date
    time: Optional[str] = "18:00:00"

class AttendanceResponse(BaseModel):
    id: UUID
    employee_id: str
    date: date
    status: str
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    check_in_location: Optional[str] = None
    check_in_lat_lng: Optional[str] = None
    check_in_photo_url: Optional[str] = None
    check_out_photo_url: Optional[str] = None
    punch_type: Optional[str] = "in_office"
    punch_note: Optional[str] = None
    session_number: Optional[int] = 1
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BreakStartRequest(BaseModel):
    employee_id: Optional[str] = None
    reason: Optional[str] = "Lunch Break"

class BreakEndRequest(BaseModel):
    break_id: UUID

class BreakResponse(BaseModel):
    id: UUID
    employee_id: str
    date: date
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reason: Optional[str] = "Lunch Break"
    duration_minutes: Optional[int] = 0

    class Config:
        from_attributes = True
