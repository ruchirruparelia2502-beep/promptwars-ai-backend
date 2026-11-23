import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "PromptWars x Cynergy AI Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS: Allow all origins for quick hackathon frontend integration
    CORS_ORIGINS: List[str] = ["*"]
    
    # AI Studio / Gemini API Key
    GEMINI_API_KEY: str = ""
    DEFAULT_GEMINI_MODEL: str = "gemini-3.8-flash"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
