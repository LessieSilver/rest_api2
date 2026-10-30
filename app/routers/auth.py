from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.db_models import User
from app.models import LoginRequest, TokenOut
from app.auth import verify_password, create_access_token

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == data.username))
    user = result.scalars().first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": str(user.id), "group": user.group.value})
    return TokenOut(access_token=token)
