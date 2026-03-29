from fasthtml.common import *
from sqlmodel import Session, select, func, col
from app.core.database import engine
from app.models import User, Role
from datetime import datetime
import json

def get_role_by_id(db_session, role_id):
    return db_session.get(Role, role_id)

def check_admin(session):
    user_id = session.get('user_id')
    if not user_id: return False
    with Session(engine) as db_session:
        user = db_session.get(User, user_id)
        if not user or not user.role or user.role.name != 'Admin':
            return False
    return True

def setup_role_routes(rt, render_nav):
    @rt('/roles', methods=['GET'])
    def list_roles(session, error: str = None):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        
        with Session(engine) as db_session:
            roles = db_session.exec(select(Role)).all()
            current_user = db_session.get(User, session.get('user_id'))
            
            role_cards = [
                Div(
                    Div(
                        H3(r.name, cls="management-card-title"),
                        Span(f"ID: {r.id}", cls="phase-status"),
                        cls="management-card-header"
                    ),
                    Div(
                        Div(Span("Skill", cls="management-card-label"), 
                            P((r.skill[:600] + "...") if r.skill and len(r.skill) > 600 else (r.skill or "No skill defined"), 
                              style="white-space: pre-wrap; margin-bottom: 0; font-size: 0.85rem;"), 
                            cls="management-card-item"),
                        cls="management-card-content"
                    ),
                    Div(
                        A("Edit", href="#", 
                          onclick=f"openRoleEditModal({r.id}, {json.dumps(r.name)}, {json.dumps(r.skill or '')})"),
                        Form(A("Delete", href="#", style="color: var(--pico-error-color);",
                               onclick=f"if(confirm('Are you sure you want to delete role \\'{r.name}\\'?')) this.closest('form').submit()"),
                             action=f"/roles/delete/{r.id}", method="post",
                             style="display: inline; margin-bottom: 0;"),
                        cls="management-card-actions"
                    ),
                    cls="management-card"
                ) for r in roles
            ]

            add_modal = Dialog(
                Article(
                    Header(H3("Add New Role")),
                    Form(
                        Label("Role Name", Input(name="name", required=True)),
                        Label("Skill (Optional)", Textarea(name="skill", rows=5)),
                        Footer(
                            Group(
                                Button("Cancel", cls="secondary", onclick="document.getElementById('role-add-modal').close()", type="button"),
                                Button("Save Role", type="submit")
                            )
                        ),
                        method="post", action="/roles/add"
                    )
                ),
                id="role-add-modal"
            )

            edit_modal = Dialog(
                Article(
                    Header(H3("Edit Role")),
                    Form(
                        Input(type="hidden", name="id", id="edit-role-id"),
                        Label("Role Name", Input(name="name", id="edit-role-name", required=True)),
                        Label("Skill (Optional)", Textarea(name="skill", id="edit-role-skill", rows=5)),
                        Footer(
                            Group(
                                Button("Cancel", cls="secondary", onclick="document.getElementById('role-edit-modal').close()", type="button"),
                                Button("Update Role", type="submit")
                            )
                        ),
                        method="post", action="/roles/edit"
                    )
                ),
                id="role-edit-modal"
            )

            js = Script("""
                function openRoleEditModal(id, name, skill) {
                    document.getElementById('edit-role-id').value = id;
                    document.getElementById('edit-role-name').value = name;
                    document.getElementById('edit-role-skill').value = skill;
                    document.getElementById('role-edit-modal').showModal();
                }
            """)

            role_css = Style("""
                @media (min-width: 768px) {
                    #role-add-modal article, #role-edit-modal article {
                        max-width: 90vw !important;
                        width: 90vw !important;
                    }
                }
                textarea[name="skill"] {
                    min-height: 400px;
                }
            """)

            return Title("Role-Skill Management"), render_nav(current_user), Main(
                js, role_css,
                Div(
                    H1("Role-Skill Management", style="margin-bottom: 0;"),
                    A("Add New Role", href="#", onclick="document.getElementById('role-add-modal').showModal()"),
                    style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;"
                ),
                Hr(),
                P(error, style="color: red;") if error else None,
                Div(*role_cards, cls="management-list"),
                add_modal,
                edit_modal,
                cls="container"
            )

    @rt('/roles/add', methods=['POST'])
    def post_add_role(session, name: str, skill: str = None):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            # Check for unique name
            existing = db_session.exec(select(Role).where(Role.name == name)).first()
            if existing:
                return list_roles(session, error="Role name already exists")
            
            new_role = Role(name=name, skill=skill)
            db_session.add(new_role)
            db_session.commit()
            return RedirectResponse('/roles', status_code=303)

    @rt('/roles/edit', methods=['POST'])
    def post_edit_role(session, id: int, name: str, skill: str = None):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            role = get_role_by_id(db_session, id)
            if not role: return RedirectResponse('/roles', status_code=303)
            
            # Check for unique name if it changed
            if name != role.name:
                existing = db_session.exec(select(Role).where(Role.name == name)).first()
                if existing:
                    return list_roles(session, error="Role name already exists")
            
            role.name = name
            role.skill = skill
            
            db_session.add(role)
            db_session.commit()
            return RedirectResponse('/roles', status_code=303)

    @rt('/roles/delete/{role_id}', methods=['POST'])
    def delete_role(session, role_id: int):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            role = db_session.get(Role, role_id)
            if not role: return RedirectResponse('/roles', status_code=303)
            
            # Check if role is assigned to any user
            user_count = db_session.exec(select(func.count(User.id)).where(User.role_id == role_id)).one()
            if user_count > 0:
                return list_roles(session, error=f"Cannot delete role '{role.name}' because it is assigned to users.")
            
            db_session.delete(role)
            db_session.commit()
            return RedirectResponse('/roles', status_code=303)
