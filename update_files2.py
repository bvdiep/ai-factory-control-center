import os
import shutil
import subprocess
import tempfile
from starlette.responses import FileResponse
from starlette.background import BackgroundTask
from fastapi import UploadFile, File, Form
from fasthtml.common import *
from sqlmodel import Session
from app.core.database import engine
from app.models import User, Project
from app.core.config import settings

def cleanup_temp_dir(temp_dir: str):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

# ...
