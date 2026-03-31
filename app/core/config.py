import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENHANDS_STORAGE_PATH: str = os.getenv("OPENHANDS_STORAGE_PATH", "./storage")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key")
    API_SECURITY_KEY: str = os.getenv("API_SECURITY_KEY", "your-default-api-key-for-external-calls")
    DB_PATH: str = os.getenv("DB_PATH", "./system.db")
    DB_NAME: str = os.getenv("DB_NAME", "aifactory")
    DB_USER: str = os.getenv("DB_USER", "aifactory")
    DB_PASS: str = os.getenv("DB_PASS", "Aifactory123456")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    PROJECT_ROOT: str = os.getenv("PROJECT_ROOT", "/home/dd/work/diep/openhands_workspace")
    MEDIA_UPLOAD_PATH: str = os.getenv("MEDIA_UPLOAD_PATH", "./uploads/bridge_media")

settings = Settings()
