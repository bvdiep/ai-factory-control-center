from fasthtml.common import *
from sqlmodel import Session, select, or_, func, col
from app.core.database import engine
from app.models import User, Role
from app.core.auth import get_password_hash
import bcrypt
from datetime import datetime
import json

def get_user_by_id(db_session, user_id):
    return db_session.exec(select(User).where(User.id == user_id)).first()

def check_admin(session):
    user_id = session.get('user_id')
    if not user_id: return False
    with Session(engine) as db_session:
        user = get_user_by_id(db_session, user_id)
        if not user or not user.role or user.role.name != 'Admin':
            return False
    return True

def setup_user_routes(rt, render_nav):
    @rt('/users', methods=['GET'])
    def list_users(session, page: int = 1, status: str = None, q: str = None, error: str = None):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        
        limit = 10
        offset = (page - 1) * limit
        
        with Session(engine) as db_session:
            query = select(User)
            if status:
                query = query.where(User.status == status)
            if q:
                query = query.where(or_(col(User.username).contains(q), col(User.name).contains(q)))
            
            # Count total
            total_query = select(func.count()).select_from(query.subquery())
            total = db_session.exec(total_query).one()
            
            # Get users with roles joined
            users = db_session.exec(query.offset(offset).limit(limit)).all()
            roles = db_session.exec(select(Role)).all()
            
            # Get current user for nav
            current_user = db_session.exec(select(User).where(User.id == session.get('user_id'))).first()
            
            # Pagination UI
            total_pages = (total + limit - 1) // limit
            pagination = Div(
                P(f"Total: {total} users"),
                Div(
                    *[A(str(p), href=f"/users?page={p}&status={status or ''}&q={q or ''}", 
                        cls="button" if p == page else "button secondary") 
                      for p in range(max(1, page-2), min(total_pages+1, page+3))],
                    cls="grid"
                ) if total_pages > 1 else None
            )

            # Filter and search UI
            filter_form = Form(
                Group(
                    Input(name="q", value=q or "", placeholder="Search username or name..."),
                    Select(
                        Option("All Status", value="", selected=not status),
                        Option("Active", value="active", selected=status == "active"),
                        Option("Inactive", value="inactive", selected=status == "inactive"),
                        name="status"
                    ),
                    Button("Search", type="submit"),
                ),
                method="get", action="/users"
            )

            user_cards = [
                Div(
                    Div(
                        H3(u.username, cls="management-card-title"),
                        Span(u.status.upper(), cls="phase-status"),
                        cls="management-card-header"
                    ),
                    Div(
                        Div(Span("Name", cls="management-card-label"), Span(u.name or "N/A"), cls="management-card-item"),
                        Div(Span("Role", cls="management-card-label"), Span(u.role.name if u.role else "N/A"), cls="management-card-item"),
                        Div(Span("ID", cls="management-card-label"), Span(str(u.id)), cls="management-card-item"),
                        cls="management-card-content"
                    ),
                    Div(
                        A("Edit", href="#", 
                          onclick=f"openUserEditModal({u.id}, {json.dumps(u.username)}, {json.dumps(u.name or '')}, {u.role_id or 'null'}, '{u.status}')"),
                        cls="management-card-actions"
                    ),
                    cls="management-card"
                ) for u in users
            ]

            add_modal = Dialog(
                Article(
                    Header(H3("Add New User")),
                    Form(
                        Label("Username", Input(name="username", required=True)),
                        Label("Name", Input(name="name")),
                        Label("Password", Input(name="password", type="password", required=True)),
                        Label("Role", Select(
                            *[Option(r.name, value=r.id) for r in roles],
                            name="role_id"
                        )),
                        Label("Status", Select(
                            Option("Active", value="active"),
                            Option("Inactive", value="inactive"),
                            name="status"
                        )),
                        Footer(
                            Group(
                                Button("Cancel", cls="secondary", onclick="document.getElementById('user-add-modal').close()", type="button"),
                                Button("Save User", type="submit")
                            )
                        ),
                        method="post", action="/users/add"
                    )
                ),
                id="user-add-modal"
            )

            edit_modal = Dialog(
                Article(
                    Header(H3("Edit User")),
                    Form(
                        Input(type="hidden", name="id", id="edit-user-id"),
                        Label("Username", Input(name="username", id="edit-username", required=True)),
                        Label("Name", Input(name="name", id="edit-name")),
                        Label("Password (leave blank to keep current)", 
                              Input(name="password", type="password")),
                        Label("Role", Select(
                            *[Option(r.name, value=r.id) for r in roles],
                            name="role_id", id="edit-role-id"
                        )),
                        Label("Status", Select(
                            Option("Active", value="active"),
                            Option("Inactive", value="inactive"),
                            name="status", id="edit-status"
                        )),
                        Footer(
                            Group(
                                Button("Cancel", cls="secondary", onclick="document.getElementById('user-edit-modal').close()", type="button"),
                                Button("Update User", type="submit")
                            )
                        ),
                        method="post", action="/users/edit"
                    )
                ),
                id="user-edit-modal"
            )

            js = Script("""
                function openUserEditModal(id, username, name, roleId, status) {
                    document.getElementById('edit-user-id').value = id;
                    document.getElementById('edit-username').value = username;
                    document.getElementById('edit-name').value = name;
                    document.getElementById('edit-role-id').value = roleId || '';
                    document.getElementById('edit-status').value = status;
                    document.getElementById('user-edit-modal').showModal();
                }
            """)

            return Title("User Management"), render_nav(current_user), Main(
                js,
                Div(
                    H1("User Management", style="margin-bottom: 0;"),
                    A("Add New User", href="#", onclick="document.getElementById('user-add-modal').showModal()"),
                    style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;"
                ),
                Hr(),
                P(error, style="color: red;") if error else None,
                filter_form,
                Div(*user_cards, cls="management-list"),
                pagination,
                add_modal,
                edit_modal,
                cls="container"
            )

    @rt('/users/add', methods=['POST'])
    def post_add_user(session, username: str, name: str, password: str, role_id: int, status: str):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            # Check for unique username
            existing = db_session.exec(select(User).where(User.username == username)).first()
            if existing:
                return list_users(session, error="Username already exists")
            
            new_user = User(
                username=username,
                name=name,
                hashed_password=get_password_hash(password),
                role_id=role_id,
                status=status
            )
            db_session.add(new_user)
            db_session.commit()
            return RedirectResponse('/users', status_code=303)

    @rt('/users/edit', methods=['POST'])
    def post_edit_user(session, id: int, username: str, name: str, password: str, role_id: int, status: str):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            user = get_user_by_id(db_session, id)
            if not user: return RedirectResponse('/users', status_code=303)
            
            # Check for unique username if it changed
            if username != user.username:
                existing = db_session.exec(select(User).where(User.username == username)).first()
                if existing:
                    return list_users(session, error="Username already exists")
            
            user.username = username
            user.name = name
            if password:
                user.hashed_password = get_password_hash(password)
            user.role_id = role_id
            user.status = status
            user.updated_at = datetime.utcnow()
            
            db_session.add(user)
            db_session.commit()
            return RedirectResponse('/users', status_code=303)
