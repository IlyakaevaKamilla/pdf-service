from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "pdf-generator-group"
    kafka_input_topic: str = "pdf-generation-requests"
    kafka_dlq_topic: str = "pdf-generation-dlq"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "pdfs"
    s3_region: str = "us-east-1"


settings = Settings()
