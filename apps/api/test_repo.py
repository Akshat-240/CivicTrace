import asyncio
from app.core.database import async_session_maker
from app.repositories.incident_repo import IncidentRepository

async def main():
    async with async_session_maker() as session:
        repo = IncidentRepository(session)
        incidents, _ = await repo.list_incidents(skip=0, limit=100)
        for i in incidents:
            print(f"INC: {i.id} Auth: {i.authority_id} -> {i.authority.id if i.authority else 'NONE'}")

asyncio.run(main())
