from sqlalchemy import Column, String, Date, Time, Text, Integer, TIMESTAMP, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class Attendance(Base):
    __tablename__ = "pharma_hrms_attendance"
    __table_args__ = (
        UniqueConstraint('employee_id', 'date', 'session_number', name='uq_emp_date_session'),
        Index('idx_attendance_emp_date', 'employee_id', 'date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(100), nullable=False, default='present')
    check_in_time = Column(Time)
    check_out_time = Column(Time)
    check_in_location = Column(Text)
    check_in_lat_lng = Column(String(50))
    check_in_photo_url = Column(Text)
    check_out_photo_url = Column(Text)
    punch_type = Column(String(50), default='in_office')
    punch_note = Column(Text)
    session_number = Column(Integer, default=1)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())


class Break(Base):
    __tablename__ = "pharma_hrms_breaks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, server_default=func.current_date())
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    reason = Column(String(100), default='Lunch Break')
    duration_minutes = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())

