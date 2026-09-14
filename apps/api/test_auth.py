from app.core.database import async_session_maker
from app.models.authority import Authority
from sqlalchemy import select
import asyncio

async def main():
    async with async_session_maker() as session:
        result = await session.execute(select(Authority))
        authorities = result.scalars().all()
        for a in authorities:
            print(f"{a.id} | {a.short_code} | {a.name}")

asyncio.run(main())
