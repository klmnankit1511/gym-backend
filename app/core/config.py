from pydantic_settings import BaseSettings
import json
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite:///./gym.db"
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
