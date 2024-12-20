from typing import Optional

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    DOCKER_BUILDER_CONTAINER: str
    API_JWT_KEY: str
    API_PORT: int = 8080
    APP_PORT: int = 3000
    APP_URL: str = ""
    APP_NAME: str
    AWS_ACCOUNT_ID: str
    AWS_REGION: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: str
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    BUCKET_NAME: str
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_HOST: Optional[str] = None
    MINIO_PORT: Optional[int] = None
    MINIO_SECRET_KEY: Optional[str] = None
    PATH_TO_DATA: Optional[str] = None
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    REACT_APP_API_PORT: int
    REACT_APP_API_URL: str
    RUN_MIGRATIONS: bool
    S3_URL: Optional[str] = None
    TOKENIZERS_PARALLELISM: str
    DEV: bool = False
    ENVIRONMENT: str

    # Uncomment the below to run alembic commands locally, or to run the db interface independently of fastapi
    # from pydantic_settings import SettingsConfigDict
    if DEV:
        model_config = SettingsConfigDict(env_file=".env")
