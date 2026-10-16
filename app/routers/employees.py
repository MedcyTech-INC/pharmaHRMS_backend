from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from typing import List, Optional, Any

from app.database.session import get_db
from app.models.employee import Employee
from app.models.leave import LeaveBalance
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    EmployeePublicResponse, EmployeeAdminResponse, ChangePasswordRequest
)
from app.dependencies.auth import get_current_user, require_admin
from app.utils.security import get_password_hash

router = APIRouter(prefix="/api/employees", tags=["Employees"])

def check_is_admin(user: Employee) -> bool:
    return (
        user.role in ["admin", "corporate_admin", "superadmin"] or
        user.hierarchy_level in ["executive", "admin", "corporate"] or
        (user.id or "").upper().startswith("ADM")
    )

@router.get("", response_model=List[Any])
async def list_employees(
    status_filter: Optional[str] = Query("active", alias="status"),
    search: Optional[str] = None,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = check_is_admin(current_user)
    stmt = select(Employee)

    if status_filter and status_filter != "all":
        stmt = stmt.where(Employee.status == status_filter)

    # Organizational Hierarchy Scoping: derive subordinate access server-side
    if not is_admin:
        if current_user.hierarchy_level == "zsm" and current_user.zone:
            stmt = stmt.where(Employee.zone == current_user.zone)
        elif current_user.hierarchy_level in ["rsm", "manager"]:
            stmt = stmt.where(
                or_(
                    Employee.reporting_to == current_user.id,
                    Employee.id == current_user.id,
                    and_(Employee.zone == current_user.zone, Employee.hierarchy_level == "be")
                )
            )

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Employee.name.ilike(search_pattern),
                Employee.email.ilike(search_pattern),
                Employee.employee_code.ilike(search_pattern),
                Employee.id.ilike(search_pattern)
            )
        )
    stmt = stmt.order_by(Employee.name)
    result = await db.execute(stmt)
    employees = result.scalars().all()

    # Mask sensitive salary and banking fields for non-admin callers
    if is_admin:
        return [EmployeeAdminResponse.model_validate(e) for e in employees]
    else:
        return [
            EmployeeAdminResponse.model_validate(e) if e.id == current_user.id
            else EmployeePublicResponse.model_validate(e)
            for e in employees
        ]

@router.get("/{employee_id}", response_model=Any)
async def get_employee(
    employee_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    is_admin = check_is_admin(current_user)
    if is_admin or current_user.id == employee_id:
        return EmployeeAdminResponse.model_validate(emp)
    return EmployeePublicResponse.model_validate(emp)

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    emp_in: EmployeeCreate,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    # Check duplicate
    stmt = select(Employee).where(or_(Employee.id == emp_in.id, Employee.email == emp_in.email))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Employee with this ID or Email already exists")

    # Hash password if not already hashed
    pwd = emp_in.password
    if not pwd.startswith("$2b$"):
        pwd = get_password_hash(pwd)

    emp_data = emp_in.model_dump()
    emp_data["password"] = pwd
    if not emp_data.get("employee_code"):
        emp_data["employee_code"] = emp_in.id

    new_emp = Employee(**emp_data)
    db.add(new_emp)

    # Initialize default leave balances
    default_balances = [
        LeaveBalance(employee_id=emp_in.id, leave_type="sick", total_allotted=6, used=0),
        LeaveBalance(employee_id=emp_in.id, leave_type="casual", total_allotted=emp_in.cl_balance or 12, used=0),
    ]
    if emp_in.gender == "female":
        default_balances.append(LeaveBalance(employee_id=emp_in.id, leave_type="maternity", total_allotted=90, used=0))
    elif emp_in.gender == "male":
        default_balances.append(LeaveBalance(employee_id=emp_in.id, leave_type="paternity", total_allotted=7, used=0))

    for b in default_balances:
        db.add(b)

    await db.commit()
    await db.refresh(new_emp)
    return new_emp

@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    emp_update: EmployeeUpdate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Non-admins can only update their own phone or dob
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level == "executive"
    if current_user.id != employee_id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to edit this employee")

    update_data = emp_update.model_dump(exclude_unset=True)
    if not is_admin:
        # Filter allowed self-edit fields
        allowed = {"phone", "dob"}
        update_data = {k: v for k, v in update_data.items() if k in allowed}

    for key, value in update_data.items():
        setattr(emp, key, value)

    await db.commit()
    await db.refresh(emp)
    return emp

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Soft delete
    emp.status = "inactive"
    await db.commit()
    return {"status": "success", "message": f"Employee {employee_id} deactivated"}

@router.post("/{employee_id}/change-password")
async def change_password(
    employee_id: str,
    body: ChangePasswordRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level == "executive"
    if current_user.id != employee_id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to change password for another user")

    stmt = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp.password = get_password_hash(body.new_password)
    await db.commit()
    return {"status": "success", "message": "Password updated successfully"}
