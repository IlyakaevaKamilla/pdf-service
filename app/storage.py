import boto3
from botocore.client import Config

from app.config import settings


class S3Storage:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Создаёт бакет, если его нет."""
        try:
            self.client.head_bucket(Bucket=settings.s3_bucket)
        except Exception:
            self.client.create_bucket(Bucket=settings.s3_bucket)

    def exists(self, key: str) -> bool:
        """Проверяет, есть ли файл. Нужно для идемпотентности."""
        try:
            self.client.head_object(Bucket=settings.s3_bucket, Key=key)
            return True
        except Exception:
            return False

    def get_presigned_url(self, key: str, expires: int = 900) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires,
        )

    def save(self, key: str, data: bytes) -> str:
        """Сохраняет файл, возвращает URL."""
        self.client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=data,
            ContentType="application/pdf",
        )
        return f"{settings.s3_endpoint_url}/{settings.s3_bucket}/{key}"


storage = S3Storage()
