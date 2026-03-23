"""Admin API routes: metrics, user management, and role assignments."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
import json

from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.models.interview import Interview
from backend.app.models.result import Result
from backend.app.schemas.user import UserResponse
from backend.app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

# --- Dependencies ---
async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency forcing the user to be an admin or super admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def get_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency forcing the user to be a super admin directly."""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin privileges required"
        )
    return current_user


# --- Endpoints ---

@router.get("/metrics", response_model=dict[str, Any])
async def get_platform_metrics(
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve platform-wide statistics for the admin dashboard."""
    # Count total users
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    
    # Count total interviews
    interview_count = (await db.execute(select(func.count(Interview.id)))).scalar() or 0
    
    # Calculate average scores
    avg_score_res = await db.execute(select(func.avg(Result.overall_score)))
    overall_avg = avg_score_res.scalar() or 0.0

    return {
        "total_users": user_count,
        "total_interviews": interview_count,
        "average_score": round(overall_avg, 2)
    }


@router.get("/users", response_model=dict[str, Any])
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all registered users across the platform."""
    count_query = await db.execute(select(func.count(User.id)))
    total = count_query.scalar() or 0

    users_query = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = list(users_query.scalars().all())

    # We reuse UserResponse but map manually if needed, or rely on fastAPI
    # We will format it properly
    user_list = [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "is_super_admin": u.is_super_admin,
            "created_at": u.created_at
        }
        for u in users
    ]

    return {
        "users": user_list,
        "total": total
    }


@router.put("/users/{target_user_id}/role")
async def modify_user_role(
    target_user_id: str,
    make_admin: bool,
    super_admin: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Promote or demote a user's admin privileges. (Super Admin Only)"""
    # Prevent self-demotion
    if target_user_id == super_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super Admin cannot modify their own admin status."
        )

    result = await db.execute(select(User).where(User.id == target_user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found"
        )

    if make_admin:
        # Enforce valid email domain rule for Admins
        if not target_user.email.endswith("@aiinterviewer.com"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only users with @aiinterviewer.com emails can become admins."
            )
        target_user.is_admin = True
    else:
        # Revoke
        target_user.is_admin = False

    await db.flush()
    await db.refresh(target_user)

    return {"message": "Role successfully updated", "is_admin": target_user.is_admin}
