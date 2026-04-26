from pydantic import BaseModel


class UploadUrlRequest(BaseModel):
    s3_key: str
    content_type: str
    expires_in: int = 3600


class DownloadUrlRequest(BaseModel):
    s3_key: str
    expires_in: int = 3600


class UploadUrlResponse(BaseModel):
    url: str
    key: str
    expires_in: int


class DownloadUrlResponse(BaseModel):
    url: str
