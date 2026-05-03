from fastapi import APIRouter, Depends

from app.api.v1.s3.schemas import (
    DownloadUrlRequest,
    DownloadUrlResponse,
    UploadUrlRequest,
    UploadUrlResponse,
)
from app.dependencies import get_s3
from app.services.s3 import S3Service

router = APIRouter(prefix="/s3", tags=["s3"])


@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(body: UploadUrlRequest, s3: S3Service = Depends(get_s3)):
    return s3.get_upload_url(body.s3_key, body.content_type, body.expires_in)


@router.post("/download-url", response_model=DownloadUrlResponse)
async def get_download_url(body: DownloadUrlRequest, s3: S3Service = Depends(get_s3)):
    url = s3.get_download_url(body.s3_key, body.expires_in)
    return DownloadUrlResponse(url=url)
