import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENHANDS_STORAGE_PATH: str = os.getenv("OPENHANDS_STORAGE_PATH", "./storage")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key")
    DB_PATH: str = os.getenv("DB_PATH", "./system.db")
    PROJECT_ROOT: str = os.getenv("PROJECT_ROOT", "/home/dd/work/diep/openhands_workspace")

settings = Settings()
