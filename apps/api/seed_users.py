import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import get_settings
from app.models.user import User
from app.models.enums import UserRole
from app.models.authority import Authority
from app.core.security import hash_password

async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    
    async with async_session() as db:
        stmt = select(Authority)
        result = await db.execute(stmt)
        auth = result.scalars().first()
        if not auth:
            auth = Authority(
                name="Demo Municipal Corporation",
                department="General Services",
                jurisdiction_level="city",
                jurisdiction_area="Lucknow",
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(auth)
            await db.commit()
            await db.refresh(auth)
            
        citizen = await db.scalar(select(User).where(User.email == "citizen@demo.local"))
        if not citizen:
            citizen = User(
                email="citizen@demo.local",
                hashed_password=hash_password("citizen123"),
                role=UserRole.CITIZEN,
                authority_id=None,
                created_at=now,
                updated_at=now
            )
            db.add(citizen)
            
        authority_user = await db.scalar(select(User).where(User.email == "authority@demo.local"))
        if not authority_user:
            authority_user = User(
                email="authority@demo.local",
                hashed_password=hash_password("authority123"),
                role=UserRole.AUTHORITY,
                authority_id=auth.id,
                created_at=now,
                updated_at=now
            )
            db.add(authority_user)
            
        admin = await db.scalar(select(User).where(User.email == "admin@demo.local"))
        if not admin:
            admin = User(
                email="admin@demo.local",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                authority_id=None,
                created_at=now,
                updated_at=now
            )
            db.add(admin)
            
        await db.commit()
        print("Demo users seeded successfully.")
        
if __name__ == "__main__":
    asyncio.run(seed())
