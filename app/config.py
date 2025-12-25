from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    # 支援 .env 中可能的拼寫錯誤
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None, validation_alias="GOOGLE_CLIENT_SERECT")
    
    BASE_URL: str = "http://localhost:8080"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
