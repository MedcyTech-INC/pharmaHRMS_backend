from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import date, datetime, time

from app.database.session import get_db
from app.models.employee import Employee
from app.models.attendance import Attendance, Break
from app.schemas.attendance import (
    ClockInRequest, ClockOutRequest, ForceCloseRequest, AttendanceResponse,
    BreakStartRequest, BreakEndRequest, BreakResponse
)
from app.dependencies.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

@router.post("/clock-in", response_model=AttendanceResponse)
async def clock_in(
    req: ClockInRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    # Non-admins can only punch for themselves
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level == "executive"
    if emp_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to clock in for another user")

    today = date.today()
    now_time = datetime.now().time()

    # 1. Active Session Check: prevent duplicate clock-in without clocking out
    active_stmt = select(Attendance).where(
        and_(
            Attendance.employee_id == emp_id,
            Attendance.date == today,
            Attendance.check_out_time.is_(None)
        )
    )
    active_res = await db.execute(active_stmt)
    existing_open = active_res.scalar_one_or_none()
    if existing_open:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee already has an active open session (#{existing_open.session_number}) for today. Please clock out before starting a new session."
        )

    # 2. Derive next session number monotonically
    stmt = select(func.coalesce(func.max(Attendance.session_number), 0)).where(
        and_(Attendance.employee_id == emp_id, Attendance.date == today)
    )
    result = await db.execute(stmt)
    max_session = result.scalar() or 0
    next_session = max_session + 1

    record = Attendance(
        employee_id=emp_id,
        date=today,
        status="Present",
        check_in_time=now_time,
        check_in_location=req.location,
        check_in_lat_lng=req.lat_lng,
        check_in_photo_url=req.photo_url,
        punch_type=req.punch_type,
        punch_note=req.punch_note,
        session_number=next_session
    )
    try:
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A concurrent clock-in session was already recorded. Please refresh."
        )

@router.post("/clock-out", response_model=AttendanceResponse)
async def clock_out(
    req: ClockOutRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level == "executive"
    if emp_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to clock out for another user")

    today = date.today()
    now_time = datetime.now().time()

    # Find open session for today
    stmt = select(Attendance).where(
        and_(
            Attendance.employee_id == emp_id,
            Attendance.date == today,
            Attendance.check_out_time.is_(None)
        )
    ).order_by(desc(Attendance.session_number))
    result = await db.execute(stmt)
    active_session = result.scalar_one_or_none()

    if not active_session:
        raise HTTPException(status_code=400, detail="No active open check-in session found for today")

    active_session.check_out_time = now_time
    if req.photo_url:
        active_session.check_out_photo_url = req.photo_url

    await db.commit()
    await db.refresh(active_session)
    return active_session

@router.post("/force-close")
async def force_close_session(
    req: ForceCloseRequest,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Attendance).where(
        and_(
            Attendance.employee_id == req.employee_id,
            Attendance.date == req.date,
            Attendance.check_out_time.is_(None)
        )
    )
    result = await db.execute(stmt)
    open_sessions = result.scalars().all()

    if not open_sessions:
        return {"status": "ok", "message": "No open sessions found to close"}

    close_time = datetime.strptime(req.time or "18:00:00", "%H:%M:%S").time()
    for s in open_sessions:
        s.check_out_time = close_time
        s.punch_note = (s.punch_note or "") + " [Forced closed by Admin]"

    await db.commit()
    return {"status": "success", "closed_sessions": len(open_sessions)}

@router.get("/records", response_model=List[AttendanceResponse])
async def list_attendance(
    employee_id: Optional[str] = None,
    target_date: Optional[date] = Query(None, alias="date"),
    month: Optional[str] = None,  # YYYY-MM
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level == "executive"
    
    stmt = select(Attendance)
    if employee_id:
        if employee_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to view other records")
        stmt = stmt.where(Attendance.employee_id == employee_id)
    elif not is_admin:
        stmt = stmt.where(Attendance.employee_id == current_user.id)

    if target_date:
        stmt = stmt.where(Attendance.date == target_date)
    elif month:
        # Filter by month 'YYYY-MM'
        start_date = datetime.strptime(f"{month}-01", "%Y-%m-%d").date()
        # Next month calculation
        m, y = (start_date.month % 12) + 1, start_date.year + (start_date.month // 12)
        end_date = date(y, m, 1)
        stmt = stmt.where(and_(Attendance.date >= start_date, Attendance.date < end_date))

    stmt = stmt.order_by(desc(Attendance.date), desc(Attendance.session_number))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/break/start", response_model=BreakResponse)
async def start_break(
    req: BreakStartRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    now = datetime.now()
    new_break = Break(
        employee_id=emp_id,
        date=now.date(),
        start_time=now,
        reason=req.reason or "Lunch Break"
    )
    db.add(new_break)
    await db.commit()
    await db.refresh(new_break)
    return new_break

@router.post("/break/end", response_model=BreakResponse)
async def end_break(
    req: BreakEndRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Break).where(Break.id == req.break_id)
    result = await db.execute(stmt)
    brk = result.scalar_one_or_none()
    if not brk:
        raise HTTPException(status_code=404, detail="Break record not found")

    now = datetime.now(brk.start_time.tzinfo if brk.start_time else None)
    brk.end_time = now
    if brk.start_time:
        duration = int((now - brk.start_time).total_seconds() / 60)
        brk.duration_minutes = max(0, duration)

    await db.commit()
    await db.refresh(brk)
    return brk
