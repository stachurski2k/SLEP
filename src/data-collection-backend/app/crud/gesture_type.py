from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.gesture_type import GestureType
from app.schemas.gesture_type import GestureTypeSchema


class GestureTypeCrud:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str) -> GestureTypeSchema:
        gesture_type = GestureType(name=name)
        self.db.add(gesture_type)
        await self.db.flush()
        await self.db.refresh(gesture_type)
        return GestureTypeSchema.model_validate(gesture_type)

    async def read(self, gesture_type_id: int) -> GestureTypeSchema | None:
        result = await self.db.get(GestureType, gesture_type_id)
        if not result:
            return None
        return GestureTypeSchema.model_validate(result)

    async def read_list(self, page: int = 0, limit: int = 100) -> list[GestureTypeSchema]:
        result = await self.db.execute(
            select(GestureType)
            .offset(page * limit)
            .limit(limit)
        )
        return [GestureTypeSchema.model_validate(row) for row in result.scalars().all()]

    async def update(self, gesture_type_id: int, name: str) -> GestureTypeSchema | None:
        gesture_type = await self.db.get(GestureType, gesture_type_id)
        if not gesture_type:
            return None
        gesture_type.name = name
        await self.db.flush()
        await self.db.refresh(gesture_type)
        return GestureTypeSchema.model_validate(gesture_type)

    async def delete(self, gesture_type_id: int) -> bool:
        gesture_type = await self.db.get(GestureType, gesture_type_id)
        if not gesture_type:
            return False
        await self.db.delete(gesture_type)
        await self.db.flush()
        return True