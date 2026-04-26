from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.exported_dataset import ExportedDataset
from app.schemas.exported_dataset import ExportedDatasetSchema


class ExportedDatasetCrud:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        filepath: str,
        videos_count: int,
        original_dataset_id: int,
        original_dataset_name: str,
        original_dataset_description: str,
    ) -> ExportedDatasetSchema:
        exported_dataset = ExportedDataset(
            filepath=filepath,
            videos_count=videos_count,
            created_at=datetime.now(timezone.utc),
            original_dataset_id=original_dataset_id,
            original_dataset_name=original_dataset_name,
            original_dataset_description=original_dataset_description,
        )
        self.db.add(exported_dataset)
        await self.db.flush()
        await self.db.refresh(exported_dataset)
        return ExportedDatasetSchema.model_validate(exported_dataset)

    async def read(self, exported_dataset_id: int) -> ExportedDatasetSchema | None:
        result = await self.db.get(ExportedDataset, exported_dataset_id)
        if not result:
            return None
        return ExportedDatasetSchema.model_validate(result)

    async def read_list(self, page: int = 0, limit: int = 100) -> list[ExportedDatasetSchema]:
        result = await self.db.execute(
            select(ExportedDataset)
            .offset(page * limit)
            .limit(limit)
        )
        return [ExportedDatasetSchema.model_validate(row) for row in result.scalars().all()]

    async def delete(self, exported_dataset_id: int) -> bool:
        exported_dataset = await self.db.get(ExportedDataset, exported_dataset_id)
        if not exported_dataset:
            return False
        await self.db.delete(exported_dataset)
        await self.db.flush()
        return True
