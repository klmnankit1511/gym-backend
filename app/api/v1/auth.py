from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.db.session import get_db
from app.models.user import User, Role
from app.models.tenant import Tenant, Branch
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.api.deps import get_current_user
from app.services.audit_log import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=UserOut)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Get or create tenant
    tenant = db.query(Tenant).filter(Tenant.slug == request.tenant_slug).first()

    if not tenant:
        # Create a new tenant if it doesn't exist
        if request.tenant_slug == "demo-gym":
            # Create demo tenant
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name="Demo Gym",
                slug="demo-gym",
                status="active"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant '{request.tenant_slug}' does not exist"
            )

    # Check if email already exists in this tenant
    existing_user = db.query(User).filter(
        User.email == request.email,
        User.tenant_id == tenant.id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in this tenant"
        )

    # Get or create MEMBER role
    member_role = db.query(Role).filter(Role.name == "MEMBER").first()
    if not member_role:
        member_role = Role(name="MEMBER")
        db.add(member_role)
        db.commit()
        db.refresh(member_role)

    # Create new user
    new_user = User(
        id=f"usr_{uuid.uuid4().hex[:8]}",
        tenant_id=tenant.id,
        email=request.email,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
    )
    new_user.roles.append(member_role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Write audit log
    write_audit_log(
        tenant_id=tenant.id,
        user_id=new_user.id,
        action="REGISTER",
        entity_type="USER",
        entity_id=new_user.id,
        metadata={"email": new_user.email}
    )

    return UserOut(
        id=new_user.id,
        tenant_id=new_user.tenant_id,
        email=new_user.email,
        full_name=new_user.full_name,
        roles=[role.name for role in new_user.roles]
    )


@router.post("/login")
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    # Find user by email (search all tenants)
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Write audit log
    write_audit_log(
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="LOGIN",
        entity_type="USER",
        entity_id=user.id
    )

    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        samesite="lax",
        secure=False  # Set True in production with HTTPS
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserOut(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            full_name=user.full_name,
            roles=[role.name for role in user.roles]
        )
    }


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    # Extract refresh token from cookies
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new access token
    access_token = create_access_token(data={"sub": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Write audit log
    write_audit_log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="LOGOUT",
        entity_type="USER",
        entity_id=current_user.id
    )

    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=[role.name for role in current_user.roles]
    )
