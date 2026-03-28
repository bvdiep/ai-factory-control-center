from fasthtml.common import *
from sqlmodel import Session, select, or_, func, col
from app.core.database import engine
from app.models import User, Role
from app.core.auth import get_password_hash
import bcrypt
from datetime import datetime


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
    def list_users(session, page: int = 1, status: str = None, q: str = None):
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

            user_rows = [
                Tr(
                    Td(u.id),
                    Td(u.username),
                    Td(u.name or ""),
                    Td(u.role.name if u.role else ""),
                    Td(u.status),
                    Td(
                        A("Edit", href=f"/users/edit/{u.id}")
                    )
                ) for u in users
            ]

            return Title("User Management"), render_nav(current_user), Main(
                Div(
                    H1("User Management", style="margin-bottom: 0;"),
                    A("Add New User", href="/users/add"),
                    style="display: flex; justify-content: space-between; align-items: center;"
                ),
                Hr(),
                filter_form,
                Table(
                    Thead(Tr(Th("ID"), Th("Username"), Th("Name"), Th("Role"), Th("Status"), Th("Actions", style="width: 120px;"))),
                    Tbody(*user_rows)
                ),
                pagination,
                cls="container"
            )

    def user_form(user=None, roles=[], error=None, current_user=None):
        title = "Edit User" if user else "Add User"
        action = f"/users/edit/{user.id}" if user else "/users/add"
        return Title(title), render_nav(current_user), Main(
            H1(title),
            P(error, style="color: red;") if error else None,
            Form(
                Label("Username", Input(name="username", value=user.username if user else "", required=True)),
                Label("Name", Input(name="name", value=(user.name or "") if user else "")),
                Label("Password" + (" (leave blank to keep current)" if user else ""), 
                      Input(name="password", type="password", required=not user)),
                Label("Role", Select(
                    *[Option(r.name, value=r.id, selected=user and r.id == user.role_id) for r in roles],
                    name="role_id"
                )),
                Label("Status", Select(
                    Option("Active", value="active", selected=user and user.status == "active"),
                    Option("Inactive", value="inactive", selected=user and user.status == "inactive"),
                    name="status"
                )),
                Button("Save User", type="submit"),
                method="post", action=action
            ),
            cls="container"
        )

    @rt('/users/add', methods=['GET'])
    def get_add_user(session):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            roles = db_session.exec(select(Role)).all()
            current_user = get_user_by_id(db_session, session.get('user_id'))
            return user_form(roles=roles, current_user=current_user)

    @rt('/users/add', methods=['POST'])
    def post_add_user(session, username: str, name: str, password: str, role_id: int, status: str):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            current_user = get_user_by_id(db_session, session.get('user_id'))
            roles = db_session.exec(select(Role)).all()
            # Check for unique username
            existing = db_session.exec(select(User).where(User.username == username)).first()
            if existing:
                return user_form(roles=roles, error="Username already exists", current_user=current_user)
            
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

    @rt('/users/edit/{user_id}', methods=['GET'])
    def get_edit_user(session, user_id: int):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            user = get_user_by_id(db_session, user_id)
            if not user: return "User not found"
            roles = db_session.exec(select(Role)).all()
            current_user = get_user_by_id(db_session, session.get('user_id'))
            return user_form(user=user, roles=roles, current_user=current_user)

    @rt('/users/edit/{user_id}', methods=['POST'])
    def post_edit_user(session, user_id: int, username: str, name: str, password: str, role_id: int, status: str):
        if not check_admin(session): return RedirectResponse('/dashboard', status_code=303)
        with Session(engine) as db_session:
            current_user = get_user_by_id(db_session, session.get('user_id'))
            roles = db_session.exec(select(Role)).all()
            user = get_user_by_id(db_session, user_id)
            if not user: return "User not found"
            
            # Check for unique username if it changed
            if username != user.username:
                existing = db_session.exec(select(User).where(User.username == username)).first()
                if existing:
                    return user_form(user=user, roles=roles, error="Username already exists", current_user=current_user)
            
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
