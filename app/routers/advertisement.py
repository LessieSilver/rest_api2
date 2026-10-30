from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.db_models import Advertisement, User, UserGroup
from app.models import AdvertisementCreate, AdvertisementUpdate, AdvertisementOut
from app.dependencies import get_current_user

router = APIRouter(prefix="/advertisement", tags=["advertisement"])


@router.post("", response_model=AdvertisementOut, status_code=201)
async def create_advertisement(
    data: AdvertisementCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ad = Advertisement(**data.model_dump(), owner_id=current_user.id)
    session.add(ad)
    await session.commit()
    await session.refresh(ad)
    return ad


@router.get("/{advertisement_id}", response_model=AdvertisementOut)
async def get_advertisement(advertisement_id: int, session: AsyncSession = Depends(get_session)):
    ad = await session.get(Advertisement, advertisement_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return ad


@router.patch("/{advertisement_id}", response_model=AdvertisementOut)
async def update_advertisement(
    advertisement_id: int,
    data: AdvertisementUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ad = await session.get(Advertisement, advertisement_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    is_owner = ad.owner_id == current_user.id
    is_admin = current_user.group == UserGroup.admin
    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Forbidden")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ad, field, value)

    await session.commit()
    await session.refresh(ad)
    return ad


@router.delete("/{advertisement_id}", status_code=204)
async def delete_advertisement(
    advertisement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ad = await session.get(Advertisement, advertisement_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    is_owner = ad.owner_id == current_user.id
    is_admin = current_user.group == UserGroup.admin
    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Forbidden")

    await session.delete(ad)
    await session.commit()


@router.get("", response_model=List[AdvertisementOut])
async def search_advertisements(
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    session: AsyncSession = Depends(get_session),
):
    conditions = []
    if title is not None:
        conditions.append(Advertisement.title.ilike(f"%{title}%"))
    if description is not None:
        conditions.append(Advertisement.description.ilike(f"%{description}%"))
    if owner_id is not None:
        conditions.append(Advertisement.owner_id == owner_id)
    if min_price is not None:
        conditions.append(Advertisement.price >= min_price)
    if max_price is not None:
        conditions.append(Advertisement.price <= max_price)

    stmt = select(Advertisement)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    result = await session.execute(stmt)
    return result.scalars().all()