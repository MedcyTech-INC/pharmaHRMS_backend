from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.database.session import get_db
from app.models.employee import Employee
from app.models.task import Task, Notification
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskApprovalRequest, TaskResponse, NotificationResponse
from app.dependencies.auth import get_current_user, require_manager_or_admin

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    assigned_to: Optional[str] = None,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level in ["executive", "zsm", "rsm", "manager"]

    stmt = select(Task)
    if assigned_to:
        stmt = stmt.where(Task.assigned_to == assigned_to)
    elif not is_admin:
        stmt = stmt.where(Task.assigned_to == current_user.id)

    stmt = stmt.order_by(desc(Task.created_at))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    req: TaskCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = Task(
        title=req.title,
        description=req.description,
        priority=req.priority or "medium",
        status="in_progress",
        due_date=req.due_date,
        assigned_to=req.assigned_to or current_user.id,
        created_by=current_user.id,
        notes=req.notes
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    req: TaskUpdate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(task, field, val)

    await db.commit()
    await db.refresh(task)
    return task

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: UUID,
    req: TaskStatusUpdate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = req.status
    if req.status == "completed":
        task.completed_at = datetime.now()
        task.approval_status = "pending"

    await db.commit()
    await db.refresh(task)
    return task

@router.post("/{task_id}/approve", response_model=TaskResponse)
async def approve_task(
    task_id: UUID,
    req: TaskApprovalRequest,
    approver: Employee = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.approval_status = "approved" if req.action == "approve" else "rejected"
    task.approval_note = req.note
    task.approved_by = approver.id

    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    current_user: Employee = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return {"status": "success", "message": "Task deleted"}

# --- NOTIFICATIONS ---
@router.get("/notifications", response_model=List[NotificationResponse])
async def list_notifications(
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(
        Notification.recipient_id == current_user.id
    ).order_by(desc(Notification.created_at))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(
        and_(Notification.id == notification_id, Notification.recipient_id == current_user.id)
    )
    result = await db.execute(stmt)
    notif = result.scalar_one_or_none()
    if notif:
        notif.is_read = True
        await db.commit()
    return {"status": "success"}
