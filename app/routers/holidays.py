from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.database.session import get_db
from app.models.holiday import Holiday
from app.schemas.holiday import HolidayResponse
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/holidays", tags=["Holidays"])

@router.get("", response_model=List[HolidayResponse])
async def list_holidays(
    year: Optional[int] = Query(2026),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Holiday)
    if year:
        stmt = stmt.where(Holiday.year == year)
    stmt = stmt.order_by(Holiday.date)
    result = await db.execute(stmt)
    return result.scalars().all()
