from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    auth_service = AuthService(db)

    user = auth_service.register(
        email=request.email,
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        is_active=user.is_active,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    auth_service = AuthService(db)

    result = auth_service.login(
        email=request.email,
        password=request.password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _, access_token = result

    return TokenResponse(
        access_token=access_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_active=current_user.is_active,
    )
