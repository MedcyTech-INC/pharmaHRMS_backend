from sqlalchemy import Column, String, Date, Time, Numeric, Integer, Boolean, JSON, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class FieldSession(Base):
    __tablename__ = "pharma_hrms_field_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    session_date = Column(Date, nullable=False, server_default=func.current_date())
    status = Column(String(50), nullable=False, default="active")
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    ended_at = Column(TIMESTAMP(timezone=True))
    start_latitude = Column(Numeric(10, 7))
    start_longitude = Column(Numeric(10, 7))
    start_address = Column(Text)
    end_latitude = Column(Numeric(10, 7))
    end_longitude = Column(Numeric(10, 7))
    end_address = Column(Text)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class FieldVisit(Base):
    __tablename__ = "pharma_hrms_field_visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True))
    employee_id = Column(String(255), nullable=False)
    assigned_by = Column(String(255))
    visit_type = Column(String(100), nullable=False, default="DOCTOR_VISIT")
    category = Column(String(50), default="doctor")
    title = Column(String(255), nullable=False)
    description = Column(Text)
    scheduled_date = Column(Date, nullable=False)
    scheduled_start = Column(String(20))
    scheduled_end = Column(String(20))
    assigned_latitude = Column(Numeric(10, 7))
    assigned_longitude = Column(Numeric(10, 7))
    assigned_address = Column(Text)
    allowed_radius_meters = Column(Integer, default=300)
    priority = Column(String(20), default="normal")
    status = Column(String(50), nullable=False, default="ASSIGNED")
    started_at = Column(TIMESTAMP(timezone=True))
    arrived_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    actual_latitude = Column(Numeric(10, 7))
    actual_longitude = Column(Numeric(10, 7))
    actual_address = Column(Text)
    arrival_distance_m = Column(Numeric(8, 2))
    duration_minutes = Column(Integer)
    proof_photo_url = Column(Text)
    completion_notes = Column(Text)
    location_exception = Column(Boolean, default=False)
    reschedule_reason = Column(Text)
    approval_status = Column(String(50), default="approved")
    approved_by = Column(String(255))
    rejection_reason = Column(Text)
    doctor_name = Column(String(255))
    clinic_name = Column(String(255))
    area = Column(String(255))
    time_slot = Column(String(50))
    visit_purpose = Column(String(255))
    products_detailed = Column(JSON, default=list)
    samples_given = Column(JSON, default=list)
    pob_amount = Column(Numeric(12, 2), default=0.00)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class FieldVisitEvent(Base):
    __tablename__ = "pharma_hrms_field_visit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True))
    session_id = Column(UUID(as_uuid=True))
    employee_id = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False)
    occurred_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    accuracy_m = Column(Numeric(8, 2))
    address = Column(Text)
    metadata_ = Column("metadata", JSON, default=dict)
    synced = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class FieldVisitProof(Base):
    __tablename__ = "pharma_hrms_field_visit_proofs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True))
    proof_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    captured_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class LocationPin(Base):
    __tablename__ = "pharma_hrms_location_pins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    visit_id = Column(UUID(as_uuid=True))
    date = Column(Date, nullable=False, server_default=func.current_date())
    pinned_at = Column(Time)
    title = Column(String(255))
    label = Column(Text)
    category = Column(String(100), default="Other")
    description = Column(Text)
    note = Column(Text)
    photo_url = Column(Text)
    location_name = Column(Text)
    pin_type = Column(String(50), default="doctor_visit")
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    address = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class DoctorSubmission(Base):
    __tablename__ = "pharma_hrms_doctor_list_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    doctor_name = Column(String(255))
    specialization = Column(String(255))
    clinic_hospital_name = Column(String(255))
    area = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    phone = Column(String(50))
    email = Column(String(255))
    preferred_time = Column(String(50))
    potential = Column(String(50), default="medium")
    status = Column(String(50), default="pending")
    submitted_by = Column(String(255))
    approved_by = Column(String(255))
    rejection_reason = Column(Text)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
