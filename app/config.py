from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # 資料庫連線網址 (Zeabur 主要使用此項)
    DATABASE_URL: str
    
    # 以下欄位設為選填，避免在雲端環境因缺少變數而崩潰
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None, validation_alias="GOOGLE_CLIENT_SERECT")
    
    BASE_URL: str = "http://localhost:8080"

        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    

    settings = Settings()

    print(f"🌍 [Config] 目前系統使用的網址 (BASE_URL): {settings.BASE_URL}")

    