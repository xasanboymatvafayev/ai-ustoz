from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/ai_ustoz_db"
    SECRET_KEY: str = "change-this-secret-key-in-production-minimum-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 kun

    class Config:
        env_file = ".env"

settings = Settings()
