"""
User profile & admin management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
from core.database import get_db
from core.dependencies import get_current_user, require_role
from core.security import hash_password
from models.user import User

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "created_at": current_user.created_at,
    }


@router.patch("/me")
async def update_me(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.full_name:
        current_user.full_name = body.full_name
    if body.password:
        if len(body.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        current_user.hashed_password = hash_password(body.password)
    await db.commit()
    await db.refresh(current_user)
    return {"id": current_user.id, "email": current_user.email, "full_name": current_user.full_name}


@router.get("/", dependencies=[Depends(require_role("admin"))])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {"id": u.id, "email": u.email, "full_name": u.full_name,
         "role": u.role, "is_active": u.is_active, "created_at": u.created_at}
        for u in users
    ]


@router.patch("/{user_id}/role", dependencies=[Depends(require_role("admin"))])
async def update_role(
    user_id: str,
    role: str,
    db: AsyncSession = Depends(get_db),
):
    valid_roles = {"admin", "analyst", "viewer"}
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of {valid_roles}")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    await db.commit()
    return {"id": user.id, "role": user.role}


@router.patch("/{user_id}/deactivate", dependencies=[Depends(require_role("admin"))])
async def deactivate_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    return {"id": user.id, "is_active": False}
