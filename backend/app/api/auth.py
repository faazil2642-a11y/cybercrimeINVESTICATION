from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserOut, TokenResponse, PasswordChange
from app.core.security import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_roles
)
from app.services.audit_service import log_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # First user is automatically ADMIN
    user_count = db.query(User).count()
    assigned_role = UserRole.ADMIN if user_count == 0 else payload.role

    new_user = User(
        full_name=payload.full_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=assigned_role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit(
        db,
        action="USER_REGISTERED",
        user_id=new_user.id,
        user_email=new_user.email,
        resource_type="USER",
        resource_id=new_user.id,
        details=f"User {new_user.email} registered with role {new_user.role.value}"
    )
    return new_user


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        log_audit(
            db,
            action="LOGIN_FAILED",
            user_email=payload.email.lower(),
            details="Invalid credentials attempt"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated."
        )

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role.value})

    log_audit(
        db,
        action="LOGIN_SUCCESS",
        user_id=user.id,
        user_email=user.email,
        resource_type="USER",
        resource_id=user.id
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed."
        )

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    log_audit(
        db,
        action="PASSWORD_CHANGED",
        user_id=current_user.id,
        user_email=current_user.email
    )
    return {"message": "Password updated successfully."}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit(
        db,
        action="LOGOUT",
        user_id=current_user.id,
        user_email=current_user.email
    )
    return {"message": "Logged out successfully."}
