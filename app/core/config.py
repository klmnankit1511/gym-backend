from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # SQL Database (Azure SQL or local SQL Server)
    database_url: str = "mssql+pymssql://sa:GymAdmin%40123%21@localhost:1433/gym_db"

    # Cosmos DB (Azure Cosmos or local emulator)
    cosmos_endpoint: str = "https://localhost:8081/"
    cosmos_key: str = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4AR0dM8s4fVOMg4aiKPAwGBA+ES-x+IB3jMEVsByKYo1F+mAGDA=="
    cosmos_database: str = "gym_audit"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    # JWT/Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # API
    api_version: str = "v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
