import asyncio
from backend.db.session import engine
from backend.models.db_models import Base

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created/verified OK")

asyncio.run(main())
