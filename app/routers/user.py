from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.db_models import User, UserGroup
from app.models import UserCreate, UserUpdate, UserOut
from app.auth import hash_password
from app.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


@router.post("", response_model=UserOut, status_code=201)
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_session)):
    if data.group == UserGroup.admin:
        result = await session.execute(select(User).where(User.group == UserGroup.admin))
        if result.scalars().first() is not None:
            raise HTTPException(status_code=403, detail="Only admin can create another admin")

    existing = await session.execute(select(User).where(User.username == data.username))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        group=data.group,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_self = current_user.id == user_id
    is_admin = current_user.group == UserGroup.admin
    if not (is_self or is_admin):
        raise HTTPException(status_code=403, detail="Forbidden")

    update_data = data.model_dump(exclude_unset=True)

    if "group" in update_data and not is_admin:
        raise HTTPException(status_code=403, detail="Only admin can change user group")

    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    if "username" in update_data:
        existing = await session.execute(
            select(User).where(User.username == update_data["username"], User.id != user_id)
        )
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Username already exists")

    for field, value in update_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_self = current_user.id == user_id
    is_admin = current_user.group == UserGroup.admin
    if not (is_self or is_admin):
        raise HTTPException(status_code=403, detail="Forbidden")

    await session.delete(user)
    await session.commit()