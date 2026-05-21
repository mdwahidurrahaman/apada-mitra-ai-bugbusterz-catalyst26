"""
Auth Routes
Registration and login endpoints backed by MongoDB Atlas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.concurrency import run_in_threadpool
from typing import Dict, Any

from app.dependencies import require_admin
from app.schemas.request_models import LoginRequest, RegisterRequest
from app.schemas.response_models import AuthResponse, UsersListResponse
from app.services.auth_service import AuthService
from app.services.database_service import DatabaseService
from app.services.user_service import UserService


router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)


@router.post(
    "/register",
    response_model=AuthResponse,
    summary="Register user",
    description="Create a user account in MongoDB Atlas"
)
async def register_user(request: RegisterRequest) -> Dict[str, Any]:
    try:
        user_service = UserService()
        user = await run_in_threadpool(
            user_service.register_user,
            name=request.name,
            email=request.email,
            password=request.password,
            phone=request.phone,
            user_type=request.user_type.value if request.user_type else None,
            location=request.location,
            lat=request.lat,
            lon=request.lon,
            enable_sms_alerts=request.enable_sms_alerts
        )
        access_token = AuthService().create_access_token(user)

        return {
            "success": True,
            "message": "Registration successful.",
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user",
    description="Authenticate a registered user by email and password"
)
async def login_user(request: LoginRequest) -> Dict[str, Any]:
    try:
        user_service = UserService()
        user = await run_in_threadpool(
            user_service.authenticate_user,
            email=request.email,
            password=request.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
        access_token = AuthService().create_access_token(user)

        return {
            "success": True,
            "message": "Login successful.",
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get(
    "/users",
    response_model=UsersListResponse,
    summary="List users",
    description="Get registered users without password hashes"
)
async def list_users(
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    try:
        user_service = UserService()
        return await run_in_threadpool(
            user_service.list_users,
            limit=limit,
            skip=skip
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get(
    "/health",
    summary="Check auth database health",
    description="Check MongoDB Atlas availability for registration/login"
)
async def auth_health_check() -> Dict[str, Any]:
    database = DatabaseService()
    configured = database.is_configured()
    connected = await run_in_threadpool(database.ping) if configured else False
    indexes_ready = (
        await run_in_threadpool(database.ensure_indexes)
        if connected
        else False
    )

    return {
        "status": "healthy" if connected and indexes_ready else "unavailable",
        "mongo_configured": configured,
        "mongo_connected": connected,
        "indexes_ready": indexes_ready,
        "message": "Auth database is ready" if connected and indexes_ready else "MongoDB Atlas is not ready"
    }
