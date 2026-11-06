from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "pdf-service"
    debug: bool = False

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "pdf-generator-group"
    kafka_input_topic: str = "pdf-generation-requests"
    kafka_dlq_topic: str = "pdf-generation-dlq"

    db_host: str = Field(validation_alias="DB_PDF_SERVICE_HOST", default="127.0.0.1")
    db_port: int = Field(validation_alias="DB_PDF_SERVICE_PORT", default=5432)
    db_name: str = Field(validation_alias="DB_PDF_SERVICE_NAME", default="rrt")
    db_user: str = Field(validation_alias="DB_PDF_SERVICE_USER", default="platform")
    db_pass: str = Field(validation_alias="DB_PDF_SERVICE_PASS", default="12345")
    db_driver: str = "postgresql"
    test_db_name: str = Field(
        validation_alias="TEST_DB_PDF_SERVICE_NAME", default="PDF_db_test"
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"{self.db_driver}://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def TEST_DATABASE_URL(self) -> str:
        return (
            f"{self.db_driver}://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.test_db_name}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        secrets_dir="/run/secrets",
    )


settings = Settings()
