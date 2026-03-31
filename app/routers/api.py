from fasthtml.common import *
from starlette.responses import JSONResponse
from sqlmodel import Session, select
from app.core.database import engine
from app.core.config import settings
from app.models import Project, Phase, User
from app.routers.projects import validate_project_path
import os
import uuid
import re
import unicodedata
from datetime import datetime

def slugify(text):
    if not text:
        return ""
    # Normalize unicode to NFD and keep ASCII only
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    # Replace special chars and spaces with _
    text = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    return text

def generate_unique_path(name):
    base_path = slugify(name)
    if not base_path:
        base_path = "project"
    # Append unique suffix
    unique_id = uuid.uuid4().hex[:8]
    return f"{base_path}_{unique_id}"

def setup_api_routes(rt):
    @rt('/api/projects', methods=['POST'])
    async def api_create_project(req):
        try:
            data = await req.json()
        except Exception as e:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        
        api_key = data.get("api_key")
        if api_key != settings.API_SECURITY_KEY:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        project_data = data.get("project")
        phases_data = data.get("phases", [])
        
        if not project_data:
            return JSONResponse({"error": "Project data is required"}, status_code=400)
        
        name = project_data.get("name")
        description = project_data.get("description")
        interview_minutes = project_data.get("interview_minutes")
        path = project_data.get("path")
        user_id = project_data.get("user_id")
        status = project_data.get("status", "active")
        
        if not name:
            return JSONResponse({"error": "Project name is required"}, status_code=400)
        
        # Auto-generate path if not provided
        if not path:
            path = generate_unique_path(name)
        
        with Session(engine) as db_session:
            # Validate project path (returns error message if already exists)
            error = validate_project_path(path, db_session)
            if error:
                return JSONResponse({"error": error}, status_code=400)
            
            # Create Project
            new_project = Project(
                name=name,
                description=description,
                interview_minutes=interview_minutes,
                path=path,
                user_id=int(user_id) if user_id else None,
                status=status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(new_project)
            db_session.flush() # To get the project ID
            
            # Create Phases
            created_phases = []
            for phase_item in phases_data:
                new_phase = Phase(
                    project_id=new_project.id,
                    order=phase_item.get("order", 0),
                    mission=phase_item.get("mission"),
                    role_id=phase_item.get("role_id"), # Now optional in model
                    user_id=int(phase_item.get("user_id")) if phase_item.get("user_id") else None,
                    # skill is removed from payload handling
                    status="Pending",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                if not new_phase.mission:
                     db_session.rollback()
                     return JSONResponse({"error": "Phase mission is required"}, status_code=400)
                
                db_session.add(new_phase)
                created_phases.append(new_phase)
            
            db_session.commit()
            
            # Refresh to get IDs
            db_session.refresh(new_project)
            
            # Create project directory
            project_dir = os.path.join(settings.PROJECT_ROOT, path)
            os.makedirs(project_dir, exist_ok=True)
            
            return JSONResponse({
                "message": "Project and phases created successfully",
                "project_id": new_project.id,
                "project_path": path,
                "phases_count": len(created_phases)
            }, status_code=201)
