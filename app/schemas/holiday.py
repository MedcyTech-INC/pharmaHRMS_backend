from pydantic import BaseModel
from datetime import date
from uuid import UUID

class HolidayResponse(BaseModel):
    id: UUID
    date: date
    day: str
    name: str
    type: str
    year: int

    class Config:
        from_attributes = True
