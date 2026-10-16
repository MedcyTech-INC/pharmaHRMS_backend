from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

from app.database.session import get_db
from app.models.employee import Employee
from app.models.field import FieldSession, FieldVisit, LocationPin, DoctorSubmission
from app.schemas.field import (
    FieldSessionStart, FieldSessionEnd, FieldVisitCreate, FieldVisitComplete,
    LocationPinCreate, DoctorSubmissionCreate, FieldVisitResponse, LocationPinResponse
)
from app.dependencies.auth import get_current_user, require_manager_or_admin

router = APIRouter(prefix="/api/field", tags=["Field Operations"])

# --- SESSIONS ---
@router.post("/sessions/start")
async def start_session(
    req: FieldSessionStart,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    now = datetime.now()
    session = FieldSession(
        employee_id=emp_id,
        session_date=now.date(),
        status="active",
        started_at=now,
        start_latitude=req.latitude,
        start_longitude=req.longitude,
        start_address=req.address,
        notes=req.notes
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"status": "success", "session_id": str(session.id)}

@router.post("/sessions/end")
async def end_session(
    req: FieldSessionEnd,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(FieldSession).where(FieldSession.id == req.session_id)
    result = await db.execute(stmt)
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Field session not found")

    sess.status = "completed"
    sess.ended_at = datetime.now()
    sess.end_latitude = req.latitude
    sess.end_longitude = req.longitude
    sess.end_address = req.address
    if req.notes:
        sess.notes = (sess.notes or "") + "\n" + req.notes

    await db.commit()
    return {"status": "success", "session_id": str(sess.id)}

# --- VISITS ---
@router.post("/visits", response_model=FieldVisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(
    req: FieldVisitCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    visit = FieldVisit(
        employee_id=emp_id,
        assigned_by=current_user.id,
        visit_type=req.visit_type,
        category=req.category,
        title=req.title,
        description=req.description,
        scheduled_date=req.scheduled_date,
        scheduled_start=req.scheduled_start,
        scheduled_end=req.scheduled_end,
        assigned_latitude=req.assigned_latitude,
        assigned_longitude=req.assigned_longitude,
        assigned_address=req.assigned_address,
        allowed_radius_meters=req.allowed_radius_meters or 300,
        priority=req.priority or "normal",
        doctor_name=req.doctor_name,
        clinic_name=req.clinic_name,
        area=req.area,
        time_slot=req.time_slot,
        visit_purpose=req.visit_purpose,
        status="ASSIGNED"
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return visit

@router.get("/visits", response_model=List[FieldVisitResponse])
async def list_visits(
    employee_id: Optional[str] = None,
    visit_date: Optional[date] = Query(None, alias="date"),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level in ["executive", "zsm", "rsm", "manager"]

    stmt = select(FieldVisit)
    if employee_id:
        if employee_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        stmt = stmt.where(FieldVisit.employee_id == employee_id)
    elif not is_admin:
        stmt = stmt.where(FieldVisit.employee_id == current_user.id)

    if visit_date:
        stmt = stmt.where(FieldVisit.scheduled_date == visit_date)

    stmt = stmt.order_by(desc(FieldVisit.scheduled_date), desc(FieldVisit.created_at))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/visits/{visit_id}/complete", response_model=FieldVisitResponse)
async def complete_visit(
    visit_id: UUID,
    req: FieldVisitComplete,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(FieldVisit).where(FieldVisit.id == visit_id)
    result = await db.execute(stmt)
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    visit.status = "COMPLETED"
    visit.completed_at = datetime.now()
    visit.actual_latitude = req.actual_latitude
    visit.actual_longitude = req.actual_longitude
    visit.actual_address = req.actual_address
    visit.arrival_distance_m = req.arrival_distance_m
    visit.duration_minutes = req.duration_minutes
    visit.proof_photo_url = req.proof_photo_url
    visit.completion_notes = req.completion_notes
    if req.products_detailed:
        visit.products_detailed = req.products_detailed
    if req.samples_given:
        visit.samples_given = req.samples_given
    if req.pob_amount is not None:
        visit.pob_amount = req.pob_amount

    await db.commit()
    await db.refresh(visit)
    return visit

# --- PINS ---
@router.post("/pins", response_model=LocationPinResponse, status_code=status.HTTP_201_CREATED)
async def create_pin(
    req: LocationPinCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    now = datetime.now()
    pin = LocationPin(
        employee_id=emp_id,
        visit_id=req.visit_id,
        date=now.date(),
        pinned_at=now.time(),
        pin_type=req.pin_type,
        label=req.label,
        title=req.title,
        category=req.category or "Other",
        description=req.description,
        note=req.note,
        photo_url=req.photo_url,
        location_name=req.location_name,
        latitude=req.latitude,
        longitude=req.longitude,
        address=req.address
    )
    db.add(pin)
    await db.commit()
    await db.refresh(pin)
    return pin

@router.get("/pins", response_model=List[LocationPinResponse])
async def list_pins(
    employee_id: Optional[str] = None,
    pin_date: Optional[date] = Query(None, alias="date"),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LocationPin)
    if employee_id:
        stmt = stmt.where(LocationPin.employee_id == employee_id)
    if pin_date:
        stmt = stmt.where(LocationPin.date == pin_date)

    stmt = stmt.order_by(desc(LocationPin.date), desc(LocationPin.pinned_at))
    result = await db.execute(stmt)
    return result.scalars().all()

# --- DOCTOR SUBMISSIONS ---
@router.post("/doctor-submissions", status_code=status.HTTP_201_CREATED)
async def create_doctor_submission(
    req: DoctorSubmissionCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    sub = DoctorSubmission(
        employee_id=emp_id,
        doctor_name=req.doctor_name,
        specialization=req.specialization,
        clinic_hospital_name=req.clinic_hospital_name,
        area=req.area,
        city=req.city,
        state=req.state,
        phone=req.phone,
        email=req.email,
        preferred_time=req.preferred_time,
        potential=req.potential or "medium",
        status="pending",
        submitted_by=current_user.id,
        notes=req.notes
    )
    db.add(sub)
    await db.commit()
    return {"status": "success", "id": str(sub.id)}
