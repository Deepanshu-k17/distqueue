from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://distqueue:distqueue@localhost:5432/distqueue"
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()