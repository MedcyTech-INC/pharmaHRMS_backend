from sqlalchemy import Column, String, Date, Integer, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class Holiday(Base):
    __tablename__ = "pharma_hrms_holidays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    day = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False, default=2026)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
