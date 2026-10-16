from sqlalchemy import Column, String, Numeric, Integer, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class OfficeLocation(Base):
    __tablename__ = "pharma_hrms_office_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    radius_meters = Column(Integer, default=500)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
