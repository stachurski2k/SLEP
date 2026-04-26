from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.datasets.schemas import DatasetRequest
from app.crud.dataset import DatasetCrud
from app.dependencies import get_db
from app.schemas.dataset import DatasetSchema

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/", response_model=DatasetSchema)
async def create_dataset(body: DatasetRequest, db: AsyncSession = Depends(get_db)):
    return await DatasetCrud(db).create(body.name, body.description)


@router.get("/", response_model=list[DatasetSchema])
async def list_datasets(page: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await DatasetCrud(db).read_list(page, limit)


@router.get("/{dataset_id}", response_model=DatasetSchema)
async def get_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    result = await DatasetCrud(db).read(dataset_id)
    if not result:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return result


@router.patch("/{dataset_id}", response_model=DatasetSchema)
async def update_dataset(dataset_id: int, body: DatasetRequest, db: AsyncSession = Depends(get_db)):
    result = await DatasetCrud(db).update(dataset_id, body.name, body.description)
    if not result:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return result


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await DatasetCrud(db).delete(dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
