from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sistema DOMO"
    
    # DB Settings (SQLite)
    DATABASE_URL: str = "sqlite+aiosqlite:///./domo_metrics.db"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_SEED: str = "DOMO_SECURE_UPLINK_PROTOCOL_2026_X"
    
    # External APIs
    NASA_API_KEY: str = "AUVRRW9j4x8RC76w9CLqLAvCNV0YgZNLcMFE0YVe"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
