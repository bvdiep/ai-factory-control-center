import os
import shutil
import subprocess
import tempfile
from starlette.responses import FileResponse
from fastapi import UploadFile, File, Form
from fasthtml.common import *
from sqlmodel import Session
from app.core.database import engine
from app.models import User, Project
from app.core.config import settings

# ... I will write the full content of files.py
