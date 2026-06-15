from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://distqueue:distqueue@localhost:5432/distqueue"


settings = Settings()