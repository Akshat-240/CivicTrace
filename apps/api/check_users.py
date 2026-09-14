import asyncio
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.user import User
async def count_users():
    async with async_session_maker() as session:
        res = await session.execute(select(User))
        users = res.scalars().all()
        print('USER_COUNT:', len(users))
        for u in users: print(u.email)
asyncio.run(count_users())
