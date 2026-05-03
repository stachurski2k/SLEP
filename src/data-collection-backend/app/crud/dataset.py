from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.dataset import Dataset
from app.schemas.dataset import DatasetSchema


class DatasetCrud:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, description: str) -> DatasetSchema:
        dataset = Dataset(name=name, description=description)
        self.db.add(dataset)
        await self.db.flush()
        await self.db.refresh(dataset)
        return DatasetSchema.model_validate(dataset)

    async def read(self, dataset_id: int) -> DatasetSchema | None:
        result = await self.db.get(Dataset, dataset_id)
        if not result:
            return None
        return DatasetSchema.model_validate(result)

    async def read_list(self, page: int = 0, limit: int = 100) -> list[DatasetSchema]:
        result = await self.db.execute(
            select(Dataset)
            .offset(page * limit)
            .limit(limit)
        )
        return [DatasetSchema.model_validate(row) for row in result.scalars().all()]

    async def update(self, dataset_id: int, name: str, description: str) -> DatasetSchema | None:
        dataset = await self.db.get(Dataset, dataset_id)
        if not dataset:
            return None
        dataset.name = name
        dataset.description = description
        await self.db.flush()
        await self.db.refresh(dataset)
        return DatasetSchema.model_validate(dataset)

    async def delete(self, dataset_id: int) -> bool:
        dataset = await self.db.get(Dataset, dataset_id)
        if not dataset:
            return False
        await self.db.delete(dataset)
        await self.db.flush()
        return True
