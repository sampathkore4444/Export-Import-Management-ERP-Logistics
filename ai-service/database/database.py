import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    ollama_url: str = "http://localhost:11434"
    ollama_text_model: str = "qwen2.5:1.5b"
    ollama_vision_model: str = "llava:7b"
    gateway_url: str = "http://localhost:8000"
    ollama_request_timeout: int = 120

settings = Settings()
