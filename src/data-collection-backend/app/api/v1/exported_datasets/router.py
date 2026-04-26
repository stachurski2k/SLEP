from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.exported_dataset import ExportedDatasetCrud
from app.dependencies import get_db
from app.schemas.exported_dataset import ExportedDatasetSchema

router = APIRouter(prefix="/exported-datasets", tags=["exported-datasets"])


@router.get("/", response_model=list[ExportedDatasetSchema])
async def list_exported_datasets(page: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await ExportedDatasetCrud(db).read_list(page, limit)


@router.get("/{exported_dataset_id}", response_model=ExportedDatasetSchema)
async def get_exported_dataset(exported_dataset_id: int, db: AsyncSession = Depends(get_db)):
    result = await ExportedDatasetCrud(db).read(exported_dataset_id)
    if not result:
        raise HTTPException(status_code=404, detail="Exported dataset not found")
    return result


@router.delete("/{exported_dataset_id}", status_code=204)
async def delete_exported_dataset(exported_dataset_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await ExportedDatasetCrud(db).delete(exported_dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Exported dataset not found")
