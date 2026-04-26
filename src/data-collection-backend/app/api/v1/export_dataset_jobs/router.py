from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.export_dataset_jobs.schemas import ExportDatasetJobCreateRequest
from app.crud.export_dataset_job import ExportDatasetJobCrud
from app.dependencies import get_db
from app.schemas.export_dataset_job import ExportDatasetJobSchema

router = APIRouter(prefix="/export-dataset-jobs", tags=["export-dataset-jobs"])


@router.post("/", response_model=ExportDatasetJobSchema)
async def create_export_dataset_job(body: ExportDatasetJobCreateRequest, db: AsyncSession = Depends(get_db)):
    return await ExportDatasetJobCrud(db).create(body.original_dataset_id)


@router.get("/", response_model=list[ExportDatasetJobSchema])
async def list_export_dataset_jobs(page: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await ExportDatasetJobCrud(db).read_list(page, limit)


@router.get("/{job_id}", response_model=ExportDatasetJobSchema)
async def get_export_dataset_job(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await ExportDatasetJobCrud(db).read(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Export dataset job not found")
    return result


@router.delete("/{job_id}", status_code=204)
async def delete_export_dataset_job(job_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await ExportDatasetJobCrud(db).delete(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Export dataset job not found")
