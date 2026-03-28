from fasthtml.common import *
from starlette.responses import Response
from sqlmodel import Session, select, or_, func, col
from app.core.database import engine
from app.core.config import settings
from app.models import User, Project, Role
from datetime import datetime
import json
import re
import os


def get_project_by_id(db_session, project_id):
    return db_session.exec(select(Project).where(Project.id == project_id)).first()


def validate_project_path(path: str, db_session, project_id=None):
    if not path:
        return "Project path cannot be empty."
    
    if not re.match(r'^[a-zA-Z0-9._-]+$', path):
        return "Project path can only contain letters, numbers, underscores, hyphens, and dots. No spaces or other special characters allowed."

    # Check for uniqueness
    query = select(Project).where(Project.path == path)
    if project_id:
        query = query.where(Project.id != project_id)
    
    existing = db_session.exec(query).first()
    if existing:
        return f"Project path '{path}' is already in use by another project."
    
    return None

def check_admin(session):
    user_id = session.get('user_id')
    if not user_id: return False
    with Session(engine) as db_session:
        user = db_session.exec(select(User).where(User.id == user_id)).first()
        if not user or not user.role or user.role.name != 'Admin':
            return False
    return True


def render_add_modal(users, error=None, values=None):
    v = values or {}
    error_el = Div(error, style="color: red; margin-bottom: 1rem;") if error else None
    return Article(
        Header(H3("Add New Project")),
        error_el,
        Form(
            Label("Name", Input(name="name", required=True, value=v.get("name", ""))),
            Label("Description", Textarea(v.get("description", ""), name="description")),
            Label("Path", Input(name="path", required=True, value=v.get("path", ""))),
            Label("Owner", Select(
                Option("Select Owner", value=""),
                *[Option(u.username, value=u.id) for u in users],
                name="user_id"
            )),
            Label("Status", Select(
                Option("Active", value="active"),
                Option("Inactive", value="inactive"),
                Option("Done", value="done"),
                name="status"
            )),
            Footer(
                Group(
                    Button("Cancel", cls="secondary", onclick="document.getElementById('add-modal').close()", type="button"),
                    Button("Save Project", type="submit")
                )
            ),
            hx_post="/projects/add", hx_target="#add-modal-inner", hx_swap="innerHTML",
            method="post", action="/projects/add"
        )
    )


def render_edit_modal(users, error=None, values=None):
    v = values or {}
    error_el = Div(error, style="color: red; margin-bottom: 1rem;") if error else None
    return Article(
        Header(H3("Edit Project")),
        error_el,
        Form(
            Input(type="hidden", name="id", id="edit-id", value=v.get("id", "")),
            Label("Name", Input(name="name", id="edit-name", required=True, value=v.get("name", ""))),
            Label("Description", Textarea(v.get("description", ""), name="description", id="edit-description")),
            Label("Path", Input(name="path", id="edit-path", required=True, value=v.get("path", ""), readonly=True)),
            Label("Owner", Select(
                Option("Select Owner", value=""),
                *[Option(u.username, value=u.id) for u in users],
                name="user_id", id="edit-user_id"
            )),
            Label("Status", Select(
                Option("Active", value="active"),
                Option("Inactive", value="inactive"),
                Option("Done", value="done"),
                name="status", id="edit-status"
            )),
            Footer(
                Group(
                    Button("Cancel", cls="secondary", onclick="document.getElementById('edit-modal').close()", type="button"),
                    Button("Update Project", type="submit")
                )
            ),
            hx_post="/projects/edit", hx_target="#edit-modal-inner", hx_swap="innerHTML",
            id="edit-form", method="post", action="/projects/edit"
        )
    )

def setup_project_routes(rt, render_nav):
    @rt('/projects', methods=['GET'])
    def list_projects(session, page: int = 1, status: str = None, q: str = None):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        
        limit = 10
        offset = (page - 1) * limit
        
        with Session(engine) as db_session:
            query = select(Project)
            if status:
                query = query.where(Project.status == status)
            if q:
                query = query.where(or_(col(Project.name).contains(q), col(Project.description).contains(q)))
            
            total = db_session.exec(select(func.count()).select_from(query.subquery())).one()
            projects = db_session.exec(query.offset(offset).limit(limit)).all()
            
            users = db_session.exec(select(User)).all()
            current_user = db_session.exec(select(User).where(User.id == session.get('user_id'))).first()
            
            total_pages = (total + limit - 1) // limit
            pagination = Div(
                P(f"Total: {total} projects"),
                Div(
                    *[A(str(p), href=f"/projects?page={p}&status={status or ''}&q={q or ''}", 
                        cls="button" if p == page else "button secondary") 
                      for p in range(max(1, page-2), min(total_pages+1, page+3))],
                    cls="grid"
                ) if total_pages > 1 else None
            )

            filter_form = Form(
                Group(
                    Input(name="q", value=q or "", placeholder="Search name or description..."),
                    Select(
                        Option("All Status", value="", selected=not status),
                        Option("Active", value="active", selected=status == "active"),
                        Option("Inactive", value="inactive", selected=status == "inactive"),
                        Option("Done", value="done", selected=status == "done"),
                        name="status"
                    ),
                    Button("Search", type="submit"),
                ),
                method="get", action="/projects"
            )

            project_rows = [
                Tr(
                    Td(p.id),
                    Td(p.name),
                    Td(p.description or ""),
                    Td(p.path),
                    Td(p.user.username if p.user else "N/A"),
                    Td(p.status),
                    Td(
                        Div(
                            A("Edit", href="#",
                                   onclick=f"openEditModal({p.id}, {json.dumps(p.name)}, {json.dumps(p.description or '')}, {json.dumps(p.path)}, {p.user_id or 'null'}, '{p.status}')"),
                            Form(A("Delete", href="#", 
                                   onclick="if(confirm('Are you sure you want to delete this project?')) this.closest('form').submit()"),
                                 action=f"/projects/delete/{p.id}", method="post",
                                 style="display: inline; margin-left: 10px;")
                        )
                    )
                ) for p in projects
            ]

            add_modal = Dialog(Div(render_add_modal(users), id="add-modal-inner"), id="add-modal")
            edit_modal = Dialog(Div(render_edit_modal(users), id="edit-modal-inner"), id="edit-modal")

            js = Script("""
                function openEditModal(id, name, description, path, userId, status) {
                    document.getElementById('edit-id').value = id;
                    document.getElementById('edit-name').value = name;
                    document.getElementById('edit-description').value = description;
                    document.getElementById('edit-path').value = path;
                    document.getElementById('edit-user_id').value = userId || '';
                    document.getElementById('edit-status').value = status;
                    document.getElementById('edit-modal').showModal();
                }
            """)

            project_css = Style("""
                #add-modal article, #edit-modal article {
                    min-width: 500px;
                    width: 60vw;
                    max-width: 700px;
                    min-height: 420px;
                }
            """)

            return Title("Project Management"), render_nav(current_user), Main(
                js, project_css,
                Div(
                    H1("Project Management", style="margin-bottom: 0;"),
                    A("Add New Project", href="#", onclick="document.getElementById('add-modal').showModal()"),
                    style="display: flex; justify-content: space-between; align-items: center;"
                ),
                Hr(),
                filter_form,
                Table(
                    Thead(Tr(Th("ID"), Th("Name"), Th("Description"), Th("Path"), Th("Owner"), Th("Status"), Th("Actions", style="width: 120px;"))),
                    Tbody(*project_rows)
                ),
                pagination,
                add_modal,
                edit_modal,
                cls="container"
            )

    @rt('/projects/add', methods=['POST'])
    def post_add_project(session, name: str, description: str, path: str, user_id: str, status: str):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            users = db_session.exec(select(User)).all()
            error = validate_project_path(path, db_session)
            if error:
                return to_xml(render_add_modal(users, error=error, values={
                    "name": name, "description": description, "path": path,
                    "user_id": user_id, "status": status
                }))
            new_project = Project(
                name=name,
                description=description,
                path=path,
                user_id=int(user_id) if user_id else None,
                status=status
            )
            db_session.add(new_project)
            db_session.commit()

            project_dir = os.path.join(settings.PROJECT_ROOT, path)
            os.makedirs(project_dir, exist_ok=True)

            return Response(content="", headers={"HX-Redirect": "/projects"})

    @rt('/projects/edit', methods=['POST'])
    def post_edit_project(session, id: int, name: str, description: str, path: str, user_id: str, status: str):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            project = get_project_by_id(db_session, id)
            if not project: return "Project not found"
            
            project.name = name
            project.description = description
            project.user_id = int(user_id) if user_id else None
            project.status = status
            project.updated_at = datetime.utcnow()
            
            db_session.add(project)
            db_session.commit()
            return Response(content="", headers={"HX-Redirect": "/projects"})

    @rt('/projects/delete/{id}', methods=['POST'])
    def post_delete_project(session, id: int):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            project = get_project_by_id(db_session, id)
            if project:
                db_session.delete(project)
                db_session.commit()
            return RedirectResponse('/projects', status_code=303)
