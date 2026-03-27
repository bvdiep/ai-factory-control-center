import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fasthtml.common import *
from sqlmodel import Session, select
from app.core.database import engine
from app.models import User, Project, Role
from app.core.auth import authenticate_user, auth_beforeware
from app.routers.users import setup_user_routes

css = Style('''
    .login-page {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 90vh;
    }
    .login-container {
        width: 100%;
        max-width: 400px;
        padding: 2rem;
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        background: var(--pico-card-background-color);
        box-shadow: var(--pico-card-sectioning-background-color) 0 1px 10px;
    }
    .login-container h1 {
        text-align: center;
    }
''')

app, rt = fast_app(
    hdrs=(css,),
    before=Beforeware(auth_beforeware, skip=['/login', '/static', '/favicon.ico']),
    secret_key="super-secret-key"
)

def render_nav(user=None):
    nav_items = [Li(A("Home", href="/dashboard", cls="secondary"))]
    if user and user.role and user.role.name == 'Admin':
        nav_items.append(Li(A("Users", href="/users", cls="secondary")))
    nav_items.append(Li(A("Logout", href="/logout", cls="secondary")))
    
    return Nav(
        Ul(Li(A(Strong("AI Factory"), href="/dashboard", cls="secondary"))),
        Ul(*nav_items),
        cls="container"
    )

setup_user_routes(rt, render_nav)
@rt('/login', methods=['GET'])
def get_login():
    return Title("Login"), Main(
        Div(
            H1("Login"),
            Form(
                Input(type="text", name="username", placeholder="Username", required=True),
                Input(type="password", name="password", placeholder="Password", required=True),
                Button("Login", type="submit"),
                action="/login", method="post"
            ),
            cls="login-container"
        ),
        cls="login-page"
    )

@rt('/login', methods=['POST'])
def post_login(username: str, password: str, session):
    user = authenticate_user(username, password)
    if user:
        session['user_id'] = user.id
        return RedirectResponse('/dashboard', status_code=303)
    return Title("Login Failed"), Main(
        Div(
            H1("Login Failed"),
            P("Invalid username or password."),
            A("Try again", href="/login", cls="contrast"),
            cls="login-container"
        ),
        cls="login-page"
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
        
        return Title("Dashboard"), render_nav(user), Main(
            H1("Dashboard"),
            Div(
                H2(f"Welcome, {user.username}!"),
                P(f"Your Role: {role.name if role else 'None'}"),
                Hr(),
                H3("Your Projects"),
                project_list if projects else P("No projects assigned.")
            ),
            cls="container"
        )

@rt('/')
def index():
    return RedirectResponse('/dashboard', status_code=303)

if __name__ == '__main__':
    serve()
