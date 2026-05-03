import os
import secrets
import logging

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from app.core.config import config

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        _cfg = Config(signature_version="s3v4", s3={"addressing_style": "path"})
        self.client = boto3.client(
            "s3",
            endpoint_url=config.s3_url,
            region_name="us-east-1",
            aws_access_key_id=config.s3_user,
            aws_secret_access_key=config.s3_password,
            config=_cfg,
        )
        self._presign_client = boto3.client(
            "s3",
            endpoint_url=config.s3_public_url,
            region_name="us-east-1",
            aws_access_key_id=config.s3_user,
            aws_secret_access_key=config.s3_password,
            config=_cfg,
        )
        self.bucket = config.s3_bucket

    def upload(self, file_path: str, s3_key: str, content_type: str = None) -> str:
        """
        Upload a local file to S3.
        Returns the S3 URL of the uploaded file.
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.client.upload_file(
                Filename=file_path,
                Bucket=self.bucket,
                Key=s3_key,
                ExtraArgs=extra_args or None,
            )
            url = f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded {file_path} to s3://{self.bucket}/{s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            raise

    def upload_bytes(self, data: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
        """
        Upload raw bytes to S3 (useful for in-memory files).
        Returns the S3 URL of the uploaded file.
        """
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=data,
                ContentType=content_type,
            )
            url = f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded bytes to s3://{self.bucket}/{s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to upload bytes to {s3_key}: {e}")
            raise

    def download(self, s3_key: str, download_path: str) -> str:
        """
        Download a file from S3 to a local path.
        Returns the local file path.
        """
        try:
            self.client.download_file(
                Bucket=self.bucket,
                Key=s3_key,
                Filename=download_path,
            )
            logger.info(f"Downloaded s3://{self.bucket}/{s3_key} to {download_path}")
            return download_path
        except ClientError as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            raise

    def download_bytes(self, s3_key: str) -> bytes:
        """
        Download a file from S3 as bytes (no local file needed).
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
            data = response["Body"].read()
            logger.info(f"Downloaded s3://{self.bucket}/{s3_key} as bytes")
            return data
        except ClientError as e:
            logger.error(f"Failed to download {s3_key} as bytes: {e}")
            raise

    def get_upload_url(self, s3_key: str, content_type: str, expires_in: int = 3600) -> dict:
        """
        Generate a presigned URL for direct client-to-S3 upload.
        A random hex prefix is prepended to the filename to avoid collisions.
        Returns a dict with 'url', 'key' (the actual key with prefix), and 'expires_in'.
        """
        prefix = secrets.token_hex(8)
        directory = os.path.dirname(s3_key)
        filename = os.path.basename(s3_key)
        prefixed_key = f"{directory}/{prefix}_{filename}" if directory else f"{prefix}_{filename}"

        try:
            url = self._presign_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": prefixed_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            logger.info(f"Generated presigned upload URL for {prefixed_key}")
            return {
                "url": url,
                "key": prefixed_key,
                "expires_in": expires_in,
            }
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            raise

    def get_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for temporary public download access.
        """
        try:
            url = self._presign_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=expires_in,
            )
            logger.info(f"Generated presigned download URL for {s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL for {s3_key}: {e}")
            raise

    def delete(self, s3_key: str) -> None:
        """Delete a file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"Deleted s3://{self.bucket}/{s3_key}")
        except ClientError as e:
            logger.error(f"Failed to delete {s3_key}: {e}")
            raise