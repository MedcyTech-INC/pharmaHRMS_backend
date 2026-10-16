from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from app.database.session import get_db
from app.models.employee import Employee
from app.models.payroll import PayrollRecord, AdvanceRequest, PayrollConfig
from app.schemas.payroll import (
    PayrollConfigRequest, SavePayslipRequest, BulkPayrollRequest,
    AdvanceApplyRequest, AdvanceActionRequest, FinalizePeriodRequest, PayrollResponse, AdvanceResponse
)
from app.dependencies.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/payroll", tags=["Payroll"])

DEFAULT_TIERS = [
    {"id": "1", "name": "Tier 1: Basic Below ₹10,000", "minSalary": 0, "maxSalary": 9999, "hra": 2000, "ma": 1500, "ca": 1000},
    {"id": "2", "name": "Tier 2: Basic Exactly ₹10,000", "minSalary": 10000, "maxSalary": 10000, "hra": 3000, "ma": 2000, "ca": 1500},
    {"id": "3", "name": "Tier 3: Basic Above ₹10,000", "minSalary": 10001, "maxSalary": 9999999, "hra": 4800, "ma": 2000, "ca": 1500}
]

def get_tiered_allowances(basic_salary: Decimal, tiers: list):
    for t in tiers:
        if Decimal(str(t["minSalary"])) <= basic_salary <= Decimal(str(t["maxSalary"])):
            return {
                "hra": Decimal(str(t["hra"])),
                "ma": Decimal(str(t["ma"])),
                "ca": Decimal(str(t["ca"]))
            }
    return {"hra": Decimal("2000"), "ma": Decimal("1500"), "ca": Decimal("1000")}

@router.get("/config")
async def get_payroll_config(
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PayrollConfig)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    config_data: Dict[str, Any] = {
        "pf_percent": 12.0,
        "professional_tax": 200.0,
        "payroll_tiers": DEFAULT_TIERS
    }
    for row in rows:
        if row.config_key == "payroll_tiers_json" and row.label:
            import json
            try:
                config_data["payroll_tiers"] = json.loads(row.label)
            except Exception:
                pass
        elif row.config_key in config_data:
            config_data[row.config_key] = float(row.config_value)

    return config_data

@router.post("/payslip", response_model=PayrollResponse)
async def save_payslip(
    req: SavePayslipRequest,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    total_allowances = sum(Decimal(str(a.get("amount", 0))) for a in req.allowances)
    total_deductions = sum(Decimal(str(d.get("amount", 0))) for d in req.deductions)

    net_pay = req.basic_pay + total_allowances - total_deductions

    stmt = select(PayrollRecord).where(
        and_(PayrollRecord.employee_id == req.employee_id, PayrollRecord.month == req.month)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        if existing.is_finalized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Payroll for {req.month} has been finalized and locked against modification."
            )
        existing.basic_pay = req.basic_pay
        existing.allowances = req.allowances
        existing.deductions = req.deductions
        existing.net_pay = net_pay
        existing.advance_money_taken = req.advance_money_taken or False
        existing.advance_money_amount = req.advance_money_amount or Decimal("0.00")
        existing.working_days = req.working_days
        existing.days_present = req.days_present
        existing.leaves_taken = req.leaves_taken
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        new_slip = PayrollRecord(
            employee_id=req.employee_id,
            month=req.month,
            basic_pay=req.basic_pay,
            allowances=req.allowances,
            deductions=req.deductions,
            net_pay=net_pay,
            advance_money_taken=req.advance_money_taken or False,
            advance_money_amount=req.advance_money_amount or Decimal("0.00"),
            working_days=req.working_days,
            days_present=req.days_present,
            leaves_taken=req.leaves_taken
        )
        db.add(new_slip)
        await db.commit()
        await db.refresh(new_slip)
        return new_slip

@router.post("/bulk-run", response_model=List[PayrollResponse])
async def run_bulk_payroll(
    req: BulkPayrollRequest,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Authoritative server-side generation of bulk monthly payroll with period lock enforcement."""
    # 1. Enforce period finalization check
    stmt_check = select(PayrollRecord).where(
        and_(PayrollRecord.month == req.month, PayrollRecord.is_finalized.is_(True))
    )
    res_check = await db.execute(stmt_check)
    if res_check.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Payroll for {req.month} has already been finalized and locked against modification."
        )

    # 2. Fetch config
    config_stmt = select(PayrollConfig)
    config_res = await db.execute(config_stmt)
    rows = config_res.scalars().all()
    pf_percent = Decimal("12.0")
    pt_amount = Decimal("200.0")
    tiers = DEFAULT_TIERS
    for row in rows:
        if row.config_key == "payroll_tiers_json" and row.label:
            import json
            try:
                tiers = json.loads(row.label)
            except Exception:
                pass
        elif row.config_key == "pf_percent":
            pf_percent = Decimal(str(row.config_value))
        elif row.config_key == "professional_tax":
            pt_amount = Decimal(str(row.config_value))

    # 3. Fetch active employees
    emp_stmt = select(Employee).where(Employee.status == "active")
    if req.employee_ids:
        emp_stmt = emp_stmt.where(Employee.id.in_(req.employee_ids))
    emp_res = await db.execute(emp_stmt)
    employees = emp_res.scalars().all()

    # 4. Fetch all active advances with installments remaining
    adv_stmt = select(AdvanceRequest).where(
        and_(
            AdvanceRequest.status == "approved",
            AdvanceRequest.installments_remaining > 0
        )
    )
    adv_res = await db.execute(adv_stmt)
    advances = adv_res.scalars().all()
    adv_by_emp: Dict[str, List[AdvanceRequest]] = {}
    for adv in advances:
        adv_by_emp.setdefault(adv.employee_id, []).append(adv)

    generated_records = []
    for emp in employees:
        emp_role = (emp.role or "").lower()
        emp_level = (emp.hierarchy_level or "").lower()
        if emp_role in ["admin", "superadmin"] and emp_level in ["executive", "corporate"]:
            continue

        basic = Decimal(str(emp.basic_salary or 0))
        tier_allowances = get_tiered_allowances(basic, tiers)
        allowances = [
            {"nameKey": "hra", "amount": float(tier_allowances["hra"])},
            {"nameKey": "medicalAllow", "amount": float(tier_allowances["ma"])},
            {"nameKey": "conveyanceAllow", "amount": float(tier_allowances["ca"])}
        ]

        pf_val = round(float(basic) * float(pf_percent) / 100)
        deductions = [
            {"nameKey": "providentFund", "amount": pf_val},
            {"nameKey": "professionalTax", "amount": float(pt_amount)}
        ]

        emp_advs = adv_by_emp.get(emp.id, [])
        advance_installment_total = Decimal("0.00")
        for a in emp_advs:
            inst = a.monthly_installment or Decimal("0.00")
            advance_installment_total += Decimal(str(inst))
            name_key = "advanceInstallment_medical" if a.advance_type == "medical" else "advanceInstallment_salary"
            deductions.append({"nameKey": name_key, "amount": float(inst)})

        tot_allow = sum(Decimal(str(a["amount"])) for a in allowances)
        tot_ded = sum(Decimal(str(d["amount"])) for d in deductions)
        net_pay = basic + tot_allow - tot_ded

        rec_stmt = select(PayrollRecord).where(
            and_(PayrollRecord.employee_id == emp.id, PayrollRecord.month == req.month)
        )
        rec_res = await db.execute(rec_stmt)
        existing = rec_res.scalar_one_or_none()

        if existing:
            if existing.is_finalized:
                continue
            existing.basic_pay = basic
            existing.allowances = allowances
            existing.deductions = deductions
            existing.net_pay = net_pay
            existing.advance_money_taken = advance_installment_total > 0
            existing.advance_money_amount = advance_installment_total
            generated_records.append(existing)
        else:
            new_rec = PayrollRecord(
                employee_id=emp.id,
                month=req.month,
                basic_pay=basic,
                allowances=allowances,
                deductions=deductions,
                net_pay=net_pay,
                advance_money_taken=advance_installment_total > 0,
                advance_money_amount=advance_installment_total
            )
            db.add(new_rec)
            generated_records.append(new_rec)

    await db.commit()
    for r in generated_records:
        await db.refresh(r)
    return generated_records

@router.get("/payslips", response_model=List[PayrollResponse])
async def list_payslips(
    month: Optional[str] = None,
    employee_id: Optional[str] = None,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level == "executive"
    stmt = select(PayrollRecord)
    if employee_id:
        if employee_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        stmt = stmt.where(PayrollRecord.employee_id == employee_id)
    elif not is_admin:
        stmt = stmt.where(PayrollRecord.employee_id == current_user.id)

    if month:
        stmt = stmt.where(PayrollRecord.month == month)

    stmt = stmt.order_by(desc(PayrollRecord.month))
    result = await db.execute(stmt)
    return result.scalars().all()

# --- ADVANCES ---
@router.post("/advances/request", response_model=AdvanceResponse, status_code=status.HTTP_201_CREATED)
async def request_advance(
    req: AdvanceApplyRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_id = req.employee_id or current_user.id
    installment = req.amount / req.repayment_months

    adv = AdvanceRequest(
        employee_id=emp_id,
        amount=req.amount,
        reason=req.reason,
        status="pending",
        repayment_months=req.repayment_months,
        monthly_installment=installment,
        installments_remaining=req.repayment_months,
        advance_type=req.advance_type
    )
    db.add(adv)
    await db.commit()
    await db.refresh(adv)
    return adv

@router.post("/advances/{advance_id}/approve", response_model=AdvanceResponse)
async def approve_advance(
    advance_id: UUID,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AdvanceRequest).where(AdvanceRequest.id == advance_id)
    result = await db.execute(stmt)
    adv = result.scalar_one_or_none()
    if not adv:
        raise HTTPException(status_code=404, detail="Advance request not found")

    adv.status = "approved"
    adv.approved_at = datetime.now()
    await db.commit()
    await db.refresh(adv)
    return adv

@router.post("/advances/{advance_id}/reject", response_model=AdvanceResponse)
async def reject_advance(
    advance_id: UUID,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AdvanceRequest).where(AdvanceRequest.id == advance_id)
    result = await db.execute(stmt)
    adv = result.scalar_one_or_none()
    if not adv:
        raise HTTPException(status_code=404, detail="Advance request not found")

    adv.status = "rejected"
    await db.commit()
    await db.refresh(adv)
    return adv

@router.get("/advances", response_model=List[AdvanceResponse])
async def list_advances(
    employee_id: Optional[str] = None,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = current_user.role in ["admin", "corporate_admin"] or current_user.hierarchy_level == "executive"
    stmt = select(AdvanceRequest)
    if employee_id:
        if employee_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        stmt = stmt.where(AdvanceRequest.employee_id == employee_id)
    elif not is_admin:
        stmt = stmt.where(AdvanceRequest.employee_id == current_user.id)

    stmt = stmt.order_by(desc(AdvanceRequest.created_at))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/finalize-period")
async def finalize_payroll_period(
    req: FinalizePeriodRequest,
    admin_user: Employee = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Finalize and freeze all payroll records for a specific month, preventing further mutations."""
    stmt = select(PayrollRecord).where(PayrollRecord.month == req.month)
    result = await db.execute(stmt)
    records = result.scalars().all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No payroll records found for month {req.month}")

    now = datetime.now()
    for rec in records:
        rec.is_finalized = True
        rec.finalized_by = admin_user.id
        rec.finalized_at = now

    await db.commit()
    return {
        "status": "success",
        "month": req.month,
        "finalized_by": admin_user.id,
        "finalized_records_count": len(records),
        "note": req.admin_note
    }
