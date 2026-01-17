from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Настройки базы данных и безопасности
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/barbershop"
    SECRET_KEY: str = "supersecretkey123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()