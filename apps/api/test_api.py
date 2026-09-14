import asyncio
from app.core.database import async_session_maker
from app.repositories.incident_repo import IncidentRepository
from app.schemas.incident import IncidentListItem

async def main():
    async with async_session_maker() as session:
        repo = IncidentRepository(session)
        incidents, _ = await repo.list_incidents(skip=0, limit=2)
        for i in incidents:
            model = IncidentListItem.model_validate(i, from_attributes=True)
            print(model.model_dump_json(indent=2))

asyncio.run(main())
