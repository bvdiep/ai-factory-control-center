import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import engine
from app.models import BridgeMessage
from sqlmodel import SQLModel
SQLModel.metadata.create_all(engine)
print("Table created")
