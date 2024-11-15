from functools import lru_cache

from scout.utils.config import Settings
from scout.utils.storage import S3StorageHandler


# Only create the settings object once
@lru_cache
def get_settings():
    return Settings(DEV=False)


settings = get_settings()


def get_s3_storage_handler(bucket: str = None):
    if bucket is None:
        bucket = settings.BUCKET_NAME

    return S3StorageHandler(
        bucket_name=bucket,
        region_name=settings.AWS_REGION,
    )
