import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fasthtml.common import *
from sqlmodel import Session, select
from app.core.database import engine
from app.models import User, Project, Role
from app.core.auth import authenticate_user, auth_beforeware

app, rt = fast_app(
    before=Beforeware(auth_beforeware, skip=['/login', '/static', '/favicon.ico']),
    secret_key="super-secret-key"
)

@rt('/login', methods=['GET'])
def get_login():
    return Titled("Login",
        Form(
            Input(type="text", name="username", placeholder="Username", required=True),
            Input(type="password", name="password", placeholder="Password", required=True),
            Button("Login", type="submit"),
            action="/login", method="post"
        )
    )

@rt('/login', methods=['POST'])
def post_login(username: str, password: str, session):
    user = authenticate_user(username, password)
    if user:
        session['user_id'] = user.id
        return RedirectResponse('/dashboard', status_code=303)
    return Titled("Login Failed",
        P("Invalid username or password."),
        A("Try again", href="/login")
    )

@rt('/logout', methods=['GET'])
def logout(session):
    session.clear()
    return RedirectResponse('/login', status_code=303)

@rt('/dashboard', methods=['GET'])
def dashboard(session):
    user_id = session.get('user_id')
    with Session(engine) as db_session:
        user = db_session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            session.clear()
            return RedirectResponse('/login', status_code=303)
        
        role = db_session.exec(select(Role).where(Role.id == user.role_id)).first()
        
        projects = user.projects
        
        project_list = Ul(
            *[Li(
                Strong(p.name), " - ", p.description, Br(),
                Small(f"Path: {p.path}")
            ) for p in projects]
        )
        
        return Titled("Dashboard",
            Div(
                H2(f"Welcome, {user.username}!"),
                P(f"Your Role: {role.name if role else 'None'}"),
                A("Logout", href="/logout"),
                Hr(),
                H3("Your Projects"),
                project_list if projects else P("No projects assigned.")
            )
        )

@rt('/')
def index():
    return RedirectResponse('/dashboard', status_code=303)

if __name__ == '__main__':
    serve()
