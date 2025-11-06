import os
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str = Field("", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = Field("postgresql+psycopg://postgres:root@localhost:5432/mealcal", env="DATABASE_URL")
    USDA_API_KEY: str = Field("", env="USDA_API_KEY")
    REDIS_URL: str = Field("", env="REDIS_URL")

    RATE_LIMIT: int = Field(15, env="RATE_LIMIT")
    RATE_LIMIT_WINDOW: int = Field(60, env="RATE_LIMIT_WINDOW")

    SSL_CERTFILE: str = Field("", env="SSL_CERTFILE")
    SSL_KEYFILE: str = Field("", env="SSL_KEYFILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
