"""
Configuration settings for the application.
"""
import os
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.
    
    These settings can be configured using environment variables.
    """
    
    # Database settings
    database_url: str = "sqlite:///./rataura.db"
    
    # Livekit settings
    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    
    # Agent settings
    voice_enabled: bool = False
    
    # LLM provider settings
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # STT provider settings
    google_stt_api_key: Optional[str] = None
    deepgram_api_key: Optional[str] = None
    
    # TTS provider settings
    google_tts_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create settings instance
settings = Settings()

