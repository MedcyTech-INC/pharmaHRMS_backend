from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.models.employee import Employee
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.security import verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. Clean email & password inputs
    clean_email = (request.email or "").strip().lower()
    clean_password = (request.password or "").strip()

    # 2. Find user by case-insensitive email
    stmt = select(Employee).where(func.lower(Employee.email) == clean_email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 3. Verify Password (handles bcrypt, plain text match, official email, or default passwords)
    user_password = (user.password or "").strip()
    user_email = (user.email or "").strip().lower()

    is_valid = False
    if user_password.startswith("$2b$"):
        is_valid = verify_password(clean_password, user_password)
    else:
        # Plain text verification aligned with frontend rules
        is_valid = (
            clean_password == user_password
            or clean_password.lower() == user_email
            or clean_password in ("password", "OrcaLabs@2026")
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if user.status not in ("active", "pending"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # 3. Generate Tokens
    token_payload = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        role=user.role
    )
