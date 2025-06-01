"""
Authentication routes for ChainFLIP user management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

from app.models.user import (
    UserRegistration, UserLogin, UserResponse, UserApproval, 
    AuthToken, AdminStats
)
from app.services.auth_service import AuthService
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()
security = HTTPBearer()

async def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    """Dependency to get auth service"""
    return AuthService(db)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """Get current authenticated user"""
    token = credentials.credentials
    return await auth_service.verify_token(token)

async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure current user is admin"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_approved_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure current user is approved"""
    if current_user["approval_status"] != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not approved"
        )
    return current_user

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserRegistration,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user (pending admin approval)"""
    try:
        user = await auth_service.register_user(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=AuthToken)
async def login_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return JWT token"""
    try:
        auth_result = await auth_service.login_user(login_data)
        return AuthToken(**auth_result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    auth_service = AuthService(None)  # We don't need DB for this conversion
    return auth_service._user_to_response(current_user)

@router.post("/logout")
async def logout_user():
    """Logout user (frontend should remove token)"""
    return {"message": "Successfully logged out"}

# Admin routes
@router.get("/admin/pending-users", response_model=List[UserResponse])
async def get_pending_users(
    admin_user: dict = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get all users pending approval (Admin only)"""
    return await auth_service.get_pending_users()

@router.get("/admin/all-users", response_model=List[UserResponse])
async def get_all_users(
    admin_user: dict = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get all users (Admin only)"""
    return await auth_service.get_all_users()

@router.post("/admin/approve-user", response_model=UserResponse)
async def approve_user(
    approval_data: UserApproval,
    admin_user: dict = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Approve or reject a user (Admin only)"""
    try:
        return await auth_service.approve_user(
            user_id=approval_data.user_id,
            approval_status=approval_data.approval_status,
            admin_id=str(admin_user["_id"]),
            admin_notes=approval_data.admin_notes
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User approval failed: {str(e)}"
        )

@router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(
    admin_user: dict = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get admin dashboard statistics (Admin only)"""
    try:
        stats = await auth_service.get_admin_stats()
        return AdminStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin stats: {str(e)}"
        )

@router.get("/admin/initialize")
async def initialize_admin_account(
    auth_service: AuthService = Depends(get_auth_service)
):
    """Initialize default admin account"""
    try:
        admin = await auth_service.initialize_admin()
        return {
            "message": "Admin account initialized",
            "admin_email": "admin@chainflip.com",
            "admin_password": "ChainFLIP2025!",
            "note": "Please change the password after first login"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize admin: {str(e)}"
        )
