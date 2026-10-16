from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.models.employee import Employee
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, TokenRefreshResponse
from app.schemas.employee import EmployeeResponse
from app.dependencies.auth import get_current_user
from app.utils.security import verify_password, get_password_hash, create_access_token, create_refresh_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. Find user by email
    stmt = select(Employee).where(Employee.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 2. Verify Password (with opportunistic migration to bcrypt)
    is_valid = False
    stored_pwd = user.password or ""
    if stored_pwd.startswith("$2b$") or stored_pwd.startswith("$2a$"):
        is_valid = verify_password(request.password, stored_pwd)
    elif stored_pwd:
        # Legacy plain-text check: if valid, immediately upgrade to salted bcrypt hash
        if request.password == stored_pwd:
            is_valid = True
            user.password = get_password_hash(request.password)
            db.add(user)
            await db.commit()
            await db.refresh(user)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if user.status != "active":
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

@router.get("/me", response_model=EmployeeResponse)
async def get_current_user_profile(
    current_user: Employee = Depends(get_current_user)
):
    """Return the authenticated current user's profile information."""
    return current_user

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a new access token using a valid refresh token."""
    try:
        from jose import jwt, JWTError
        from app.config import settings
        payload = jwt.decode(request.refresh_token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    stmt = select(Employee).where(Employee.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    new_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return TokenRefreshResponse(access_token=new_token)
