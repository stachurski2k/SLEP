from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.gesture_class import GestureClass
from app.schemas.gesture_class import GestureClassSchema


class GestureClassCrud:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str) -> GestureClassSchema:
        gesture_class = GestureClass(name=name)
        self.db.add(gesture_class)
        await self.db.flush()
        await self.db.refresh(gesture_class)
        return GestureClassSchema.model_validate(gesture_class)

    async def read(self, gesture_class_id: int) -> GestureClassSchema | None:
        result = await self.db.get(GestureClass, gesture_class_id)
        if not result:
            return None
        return GestureClassSchema.model_validate(result)

    async def read_list(self, page: int = 0, limit: int = 100) -> list[GestureClassSchema]:
        result = await self.db.execute(
            select(GestureClass)
            .offset(page * limit)
            .limit(limit)
        )
        return [GestureClassSchema.model_validate(row) for row in result.scalars().all()]

    async def update(self, gesture_class_id: int, name: str) -> GestureClassSchema | None:
        gesture_class = await self.db.get(GestureClass, gesture_class_id)
        if not gesture_class:
            return None
        gesture_class.name = name
        await self.db.flush()
        await self.db.refresh(gesture_class)
        return GestureClassSchema.model_validate(gesture_class)

    async def delete(self, gesture_class_id: int) -> bool:
        gesture_class = await self.db.get(GestureClass, gesture_class_id)
        if not gesture_class:
            return False
        await self.db.delete(gesture_class)
        await self.db.flush()
        return True