from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.import_video_jobs.schemas import ImportVideoJobCreateRequest
from app.crud.import_video_job import ImportVideoJobCrud
from app.dependencies import get_db
from app.schemas.import_video_job import ImportVideoJobSchema

router = APIRouter(prefix="/import-video-jobs", tags=["import-video-jobs"])


@router.post("/", response_model=ImportVideoJobSchema)
async def create_import_video_job(body: ImportVideoJobCreateRequest, db: AsyncSession = Depends(get_db)):
    return await ImportVideoJobCrud(db).create(
        body.video_name, body.video_filepath, body.video_description, body.dataset_id
    )


@router.get("/", response_model=list[ImportVideoJobSchema])
async def list_import_video_jobs(page: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await ImportVideoJobCrud(db).read_list(page, limit)


@router.get("/{job_id}", response_model=ImportVideoJobSchema)
async def get_import_video_job(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await ImportVideoJobCrud(db).read(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Import video job not found")
    return result


@router.delete("/{job_id}", status_code=204)
async def delete_import_video_job(job_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await ImportVideoJobCrud(db).delete(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Import video job not found")
