from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.db_models import User


async def get_or_create_user(phone: str, name: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if not user:
        user = User(phone=phone, name=name)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif user.name != name and name != phone:
        user.name = name
        await db.commit()
        await db.refresh(user)

    return user
