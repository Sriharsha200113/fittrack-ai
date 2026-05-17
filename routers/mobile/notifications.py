from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.db.session import get_db
from backend.core.deps import get_current_user
from backend.models.db_models import User, DeviceToken

router = APIRouter(prefix="/notifications", tags=["notifications"])


class RegisterRequest(BaseModel):
    token: str
    platform: str = "ios"


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_device(
    body: RegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(DeviceToken).where(DeviceToken.token == body.token)
    )
    if existing.scalar_one_or_none():
        return {"message": "Already registered"}

    device = DeviceToken(user_id=current_user.id, token=body.token, platform=body.platform)
    db.add(device)
    await db.commit()
    return {"message": "Device registered"}


@router.delete("/unregister")
async def unregister_device(
    body: RegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeviceToken).where(DeviceToken.token == body.token, DeviceToken.user_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.is_active = False
    await db.commit()
    return {"message": "Device unregistered"}
