from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres.gtjoxpzthofyowatxsst:A5S7VjKPnpxPTezD@aws-1-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
    
    # JWT
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # App
    app_name: str = "Quiz Programming API"
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()