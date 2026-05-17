import random
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from backend.db.session import get_db
from backend.models.db_models import User, OTPCode
from backend.core.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_EXPIRE_MINUTES = 10


class SendOTPRequest(BaseModel):
    phone: str


class VerifyOTPRequest(BaseModel):
    phone: str
    code: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _normalize_phone(phone: str) -> str:
    return phone.strip().lstrip('+')


@router.post("/send-otp")
async def send_otp(body: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    phone = _normalize_phone(body.phone)
    code = "".join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    otp = OTPCode(phone=phone, code=code, expires_at=expires_at)
    db.add(otp)
    await db.commit()
    # In production, send via SMS. For now, return code in dev mode.
    return {"message": "OTP sent", "dev_code": code}


@router.post("/verify-otp")
async def verify_otp(body: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    phone = _normalize_phone(body.phone)
    result = await db.execute(
        select(OTPCode)
        .where(OTPCode.phone == phone, OTPCode.code == body.code, OTPCode.used == False)
        .order_by(OTPCode.created_at.desc())
    )
    otp = result.scalar_one_or_none()
    if not otp or otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")

    otp.used = True

    user_result = await db.execute(select(User).where(User.phone == phone))
    user = user_result.scalar_one_or_none()
    if not user:
        user = User(phone=phone)
        db.add(user)

    await db.commit()
    await db.refresh(user)

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "user_id": str(user.id),
        "name": user.name,
    }


@router.post("/refresh")
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    return {"access_token": create_access_token(user_id)}
