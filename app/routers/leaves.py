from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import date, timedelta
from uuid import UUID

from app.database.session import get_db
from app.models.employee import Employee
from app.models.leave import LeaveRequest, LeaveBalance, MonthlyLeaveQuota
from app.models.attendance import Attendance
from app.schemas.leave import (
    LeaveApplyRequest, LeaveActionRequest, LeaveBalanceUpdate,
    LeaveResponse, LeaveBalanceResponse, MonthlyQuotaResponse
)
from app.dependencies.auth import get_current_user, require_admin, require_manager_or_admin

router = APIRouter(prefix="/api/leaves", tags=["Leaves"])

@router.post("/apply", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
async def apply_leave(
    req: LeaveApplyRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    if req.to_date < req.from_date:
        raise HTTPException(status_code=400, detail="to_date must be on or after from_date")

    leave_req = LeaveRequest(
        employee_id=emp_id,
        leave_type=req.leave_type,
        from_date=req.from_date,
        to_date=req.to_date,
        reason=req.reason,
        status="pending"
    )
    db.add(leave_req)
    await db.commit()
    await db.refresh(leave_req)
    return leave_req

@router.post("/{request_id}/approve", response_model=LeaveResponse)
async def approve_leave(
    request_id: UUID,
    body: Optional[LeaveActionRequest] = None,
    approver: Employee = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    is_admin = (
        approver.role in ["admin", "corporate_admin", "superadmin"] or
        approver.hierarchy_level in ["executive", "admin", "corporate"] or
        (approver.id or "").upper().startswith("ADM")
    )

    # 1. Prevent self-approval
    if req.employee_id == approver.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot approve your own leave request"
        )

    # 2. Enforce organizational reporting hierarchy
    if not is_admin:
        emp_stmt = select(Employee).where(Employee.id == req.employee_id)
        emp_res = await db.execute(emp_stmt)
        target_emp = emp_res.scalar_one_or_none()
        if target_emp:
            in_scope = (
                target_emp.reporting_to == approver.id or
                (approver.hierarchy_level == "zsm" and target_emp.zone == approver.zone) or
                (approver.hierarchy_level in ["rsm", "manager"] and target_emp.territory == approver.territory)
            )
            if not in_scope:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to approve leave for employees outside your reporting hierarchy"
                )

    if req.status == "Approved":
        return req

    req.status = "Approved"
    req.admin_note = body.admin_note if body else None
    req.approved_by = approver.id

    # Calculate days count
    diff_days = (req.to_date - req.from_date).days + 1

    # Atomic Update: Decrement/increment leave balances
    bal_stmt = select(LeaveBalance).where(
        and_(LeaveBalance.employee_id == req.employee_id, LeaveBalance.leave_type == req.leave_type)
    )
    bal_res = await db.execute(bal_stmt)
    bal = bal_res.scalar_one_or_none()
    if bal:
        bal.used += diff_days
    else:
        new_bal = LeaveBalance(
            employee_id=req.employee_id,
            leave_type=req.leave_type,
            total_allotted=0,
            used=diff_days
        )
        db.add(new_bal)

    # Atomic Update: Auto-mark attendance days as 'Leave'
    curr_date = req.from_date
    while curr_date <= req.to_date:
        att_stmt = select(Attendance).where(
            and_(Attendance.employee_id == req.employee_id, Attendance.date == curr_date)
        )
        att_res = await db.execute(att_stmt)
        att = att_res.scalar_one_or_none()
        if att:
            att.status = "Leave"
        else:
            db.add(Attendance(
                employee_id=req.employee_id,
                date=curr_date,
                status="Leave"
            ))
        curr_date += timedelta(days=1)

    await db.commit()
    await db.refresh(req)
    return req

@router.post("/{request_id}/reject", response_model=LeaveResponse)
async def reject_leave(
    request_id: UUID,
    body: Optional[LeaveActionRequest] = None,
    approver: Employee = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    is_admin = (
        approver.role in ["admin", "corporate_admin", "superadmin"] or
        approver.hierarchy_level in ["executive", "admin", "corporate"] or
        (approver.id or "").upper().startswith("ADM")
    )

    if not is_admin:
        emp_stmt = select(Employee).where(Employee.id == req.employee_id)
        emp_res = await db.execute(emp_stmt)
        target_emp = emp_res.scalar_one_or_none()
        if target_emp:
            in_scope = (
                target_emp.reporting_to == approver.id or
                (approver.hierarchy_level == "zsm" and target_emp.zone == approver.zone) or
                (approver.hierarchy_level in ["rsm", "manager"] and target_emp.territory == approver.territory)
            )
            if not in_scope:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to reject leave for employees outside your reporting hierarchy"
                )

    req.status = "Rejected"
    req.admin_note = body.admin_note if body else None
    req.approved_by = approver.id

    await db.commit()
    await db.refresh(req)
    return req

@router.get("/requests", response_model=List[LeaveResponse])
async def list_leave_requests(
    employee_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level in ["executive", "zsm", "rsm", "manager"]

    stmt = select(LeaveRequest)
    if employee_id:
        if employee_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        stmt = stmt.where(LeaveRequest.employee_id == employee_id)
    elif not is_admin:
        stmt = stmt.where(LeaveRequest.employee_id == current_user.id)

    if status_filter:
        stmt = stmt.where(LeaveRequest.status.ilike(status_filter))

    stmt = stmt.order_by(desc(LeaveRequest.created_at))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/balances/{employee_id}", response_model=List[LeaveBalanceResponse])
async def get_leave_balances(
    employee_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level == "executive"
    if employee_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    stmt = select(LeaveBalance).where(LeaveBalance.employee_id == employee_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/balances/{employee_id}", response_model=LeaveBalanceResponse)
async def update_leave_balance(
    employee_id: str,
    update_in: LeaveBalanceUpdate,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LeaveBalance).where(
        and_(LeaveBalance.employee_id == employee_id, LeaveBalance.leave_type == update_in.leave_type)
    )
    result = await db.execute(stmt)
    bal = result.scalar_one_or_none()

    if bal:
        bal.total_allotted = update_in.total_allotted
        bal.used = update_in.used
    else:
        bal = LeaveBalance(
            employee_id=employee_id,
            leave_type=update_in.leave_type,
            total_allotted=update_in.total_allotted,
            used=update_in.used
        )
        db.add(bal)

    await db.commit()
    await db.refresh(bal)
    return bal

@router.get("/quota/{employee_id}", response_model=MonthlyQuotaResponse)
async def get_monthly_quota(
    employee_id: str,
    month: Optional[str] = None,  # YYYY-MM
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    target_month = month or date.today().strftime("%Y-%m")

    stmt = select(MonthlyLeaveQuota).where(
        and_(MonthlyLeaveQuota.employee_id == employee_id, MonthlyLeaveQuota.month == target_month)
    )
    result = await db.execute(stmt)
    quota = result.scalar_one_or_none()

    if not quota:
        quota = MonthlyLeaveQuota(
            employee_id=employee_id,
            month=target_month,
            allotted=3,
            used=0
        )
        db.add(quota)
        await db.commit()
        await db.refresh(quota)

    return MonthlyQuotaResponse(
        id=quota.id,
        employee_id=quota.employee_id,
        month=quota.month,
        allotted=quota.allotted,
        used=quota.used,
        remaining=quota.allotted - quota.used
    )
