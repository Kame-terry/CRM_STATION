from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    # 資料庫連線網址
    DATABASE_URL: str = ""
    
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None, validation_alias="GOOGLE_CLIENT_SERECT")
    
    # 強制優先讀取系統環境變數中的 BASE_URL，若無則預設 localhost
    BASE_URL: str = Field("http://localhost:8080", validation_alias="BASE_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# 手動檢查環境變數以確保 Zeabur 的變數有被系統抓到
env_base_url = os.getenv("BASE_URL")
if env_base_url:
    print(f"🌟 [System ENV] 偵測到系統環境變數 BASE_URL: {env_base_url}")

settings = Settings()

# 如果環境變數存在，強制覆蓋 settings 裡的預設值
if env_base_url:
    settings.BASE_URL = env_base_url.rstrip('/')

print(f"🌍 [Config Result] 最終使用的網址: {settings.BASE_URL}")