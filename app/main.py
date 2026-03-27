import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fasthtml.common import *
from sqlmodel import Session, select
from app.core.database import engine
from app.models import User, Project, Role, Phase
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
                Strong(A(p.name, href=f"/projects/{p.id}")), " - ", p.description, Br(),
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


@rt('/projects/{id}')
def project_detail(id: int, session):
    user_id = session.get('user_id')
    with Session(engine) as db_session:
        user = db_session.exec(select(User).where(User.id == user_id)).first()
        project = db_session.exec(select(Project).where(Project.id == id)).first()
        if not project: return RedirectResponse('/dashboard', status_code=303)
        
        # Check if user has access to project
        is_admin = user.role and user.role.name == 'Admin'
        if not is_admin and project not in user.projects:
             return RedirectResponse('/dashboard', status_code=303)

        phases = db_session.exec(select(Phase).where(Phase.project_id == id).order_by(Phase.order)).all()
        roles = db_session.exec(select(Role)).all()
        users = db_session.exec(select(User)).all()
        
        phase_rows = [Tr(
            Td(p.order),
            Td(p.mission[:50] + "..." if len(p.mission) > 50 else p.mission),
            Td(p.role.name if p.role else "N/A"),
            Td(p.user.username if p.user else "Unassigned"),
            Td(p.status),
            Td(A("Details", href=f"/projects/{id}/phases/{p.id}", cls="button outline")),
            Td(A("Edit", href=f"/projects/{id}/phases/{p.id}/edit", cls="button") if p.status == 'pending' else "")
        ) for p in phases]
        
        add_phase_modal = Dialog(
            Article(
                Header(H3("Add New Phase")),
                Form(
                    Grid(
                        Label("Order", Input(type="number", name="order", placeholder="Order", required=True)),
                        Label("Role", Select(*[Option(r.name, value=r.id) for r in roles], name="role_id", required=True)),
                    ),
                    Label("Mission", Textarea(name="mission", placeholder="Mission", required=True, rows=4)),
                    Label("User (Optional)", Select(Option("Select User", value=""), *[Option(u.username, value=u.id) for u in users], name="user_id")),
                    Footer(
                        Grid(
                            Button("Cancel", cls="secondary", onclick="document.getElementById('add-phase-modal').close()", type="button"),
                            Button("Add Phase", type="submit")
                        )
                    ),
                    action=f"/projects/{id}/phases", method="post"
                ),
            ),
            id="add-phase-modal"
        )
        
        user_roles = {u.id: u.role_id for u in users}
        js = Script(f"""
            const userRoles = {json.dumps(user_roles)};
            function checkRoleMismatch(event) {{
                const form = event.target;
                const userIdSelect = form.querySelector('[name="user_id"]');
                const roleIdSelect = form.querySelector('[name="role_id"]');
                if (!userIdSelect || !roleIdSelect) return;
                
                const userId = userIdSelect.value;
                const roleId = roleIdSelect.value;
                if (userId && userRoles[userId] != roleId) {{
                    alert("Warning: Selected user's role does not match phase role.");
                }}
            }}
            document.addEventListener('submit', checkRoleMismatch);
        """)
        
        return Title(f"Project: {project.name}"), render_nav(user), Main(
            js,
            H1(f"Project: {project.name}"),
            Div(
                P(Strong("Description: "), project.description),
                P(Strong("Path: "), project.path),
                P(Strong("Status: "), project.status),
            ),
            Hr(),
            Grid(
                H2("Phases"),
                Div(A("Add Phase", href="#", onclick="document.getElementById('add-phase-modal').showModal(); return false;"), style="text-align: right;")
            ),
            Table(
                Thead(Tr(Th("Order"), Th("Mission"), Th("Role"), Th("User"), Th("Status"), Th("Actions"), Th(""))),
                Tbody(*phase_rows)
            ) if phases else P("No phases yet."),
            add_phase_modal,
            cls="container"
        )

@rt('/projects/{project_id}/phases', methods=['POST'])
def add_phase(project_id: int, order: int, mission: str, role_id: int, user_id: str, session):
    with Session(engine) as db_session:
        # Check order constraint
        next_phase = db_session.exec(
            select(Phase)
            .where(Phase.project_id == project_id)
            .where(Phase.order > order)
            .order_by(Phase.order)
        ).first()
        
        if next_phase and next_phase.status != 'pending':
            return Title("Error"), Main(H1("Error"), P("Cannot add phase before a phase that is already started/done."), A("Back", href=f"/projects/{project_id}"))

        new_phase = Phase(
            project_id=project_id,
            order=order,
            mission=mission,
            role_id=role_id,
            user_id=int(user_id) if user_id else None,
            skill=None,
            status="pending"
        )
        db_session.add(new_phase)
        db_session.commit()
        return RedirectResponse(f'/projects/{project_id}', status_code=303)

@rt('/projects/{project_id}/phases/{phase_id}')
def phase_detail(project_id: int, phase_id: int, session):
    user_id = session.get('user_id')
    with Session(engine) as db_session:
        user = db_session.get(User, user_id)
        phase = db_session.get(Phase, phase_id)
        project = db_session.get(Project, project_id)
        if not phase: return RedirectResponse(f'/projects/{project_id}', status_code=303)
        
        metrics_bar = Grid(
            Div(Small(Span("Token In: ", style="color: #666;"), Strong(phase.token_in)), style="background: #f0f4f8; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Token Out: ", style="color: #666;"), Strong(phase.token_out)), style="background: #fffbeb; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Cache Hit: ", style="color: #666;"), Strong(phase.cache_hit)), style="background: #f0fdf4; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Reasoning: ", style="color: #666;"), Strong(phase.reasoning)), style="background: #f5f3ff; padding: 0.5rem; border-radius: 8px; text-align: center;"),
        )
        
        project_phase_info = Article(
            Grid(
                Div(
                    H4("Project"),
                    P(Strong("Name: "), project.name if project else "N/A"),
                    P(Strong("Description: "), (project.description or "N/A") if project else "N/A"),
                    P(Strong("Path: "), project.path if project else "N/A"),
                    P(Strong("Status: "), project.status if project else "N/A"),
                ),
                Div(
                    H4("Phase Info"),
                    P(Strong("Role: "), phase.role.name if phase.role else "N/A"),
                    P(Strong("User: "), phase.user.username if phase.user else "Unassigned"),
                    P(Strong("Status: "), phase.status),
                )
            )
        )
        
        return Title("Phase Details"), render_nav(user), Main(
            H1(f"Phase Detail (Order: {phase.order})"),
            metrics_bar,
            project_phase_info,
            Article(
                H2("Mission"),
                P(phase.mission),
                H2("Skill"),
                P(phase.skill or "No skills defined"),
                H2("Logging"),
                Pre(phase.logging or "No logs"),
                Footer(A("Back to Project", href=f"/projects/{project_id}", cls="button"))
            ),
            cls="container"
        )

@rt('/projects/{project_id}/phases/{phase_id}/edit', methods=['GET'])
def edit_phase_get(project_id: int, phase_id: int, session):
    user_id = session.get('user_id')
    with Session(engine) as db_session:
        user = db_session.get(User, user_id)
        phase = db_session.get(Phase, phase_id)
        if not phase or phase.status != 'pending':
            return RedirectResponse(f'/projects/{project_id}', status_code=303)
        
        roles = db_session.exec(select(Role)).all()
        users = db_session.exec(select(User)).all()
        
        user_roles = {u.id: u.role_id for u in users}
        js = Script(f"""
            const userRoles = {json.dumps(user_roles)};
            function checkRoleMismatch(event) {{
                const form = event.target;
                const userIdSelect = form.querySelector('[name="user_id"]');
                const roleIdSelect = form.querySelector('[name="role_id"]');
                if (!userIdSelect || !roleIdSelect) return;
                
                const userId = userIdSelect.value;
                const roleId = roleIdSelect.value;
                if (userId && userRoles[userId] != roleId) {{
                    alert("Warning: Selected user's role does not match phase role.");
                }}
            }}
            document.addEventListener('submit', checkRoleMismatch);
        """)
        
        return Title("Edit Phase"), render_nav(user), Main(
            js,
            H1("Edit Phase"),
            Form(
                Grid(
                    Label("Order", Input(type="number", name="order", value=phase.order, required=True)),
                    Label("Role", Select(*[Option(r.name, value=r.id, selected=(r.id == phase.role_id)) for r in roles], name="role_id", required=True)),
                ),
                Label("Mission", Textarea(phase.mission, name="mission", required=True, rows=4)),
                Label("User (Optional)", Select(Option("Select User", value=""), *[Option(u.username, value=u.id, selected=(u.id == phase.user_id)) for u in users], name="user_id")),
                Label("Skill", Textarea(phase.skill or "", name="skill", rows=4)),
                Grid(
                    A("Cancel", href=f"/projects/{project_id}", cls="button secondary"),
                    Button("Update Phase", type="submit")
                ),
                action=f"/projects/{project_id}/phases/{phase_id}/edit", method="post"
            ),
            cls="container"
        )

@rt('/projects/{project_id}/phases/{phase_id}/edit', methods=['POST'])
def edit_phase_post(project_id: int, phase_id: int, order: int, mission: str, role_id: int, user_id: str, skill: str, session):
    with Session(engine) as db_session:
        phase = db_session.get(Phase, phase_id)
        if not phase or phase.status != 'pending':
            return RedirectResponse(f'/projects/{project_id}', status_code=303)
        
        phase.order = order
        phase.mission = mission
        phase.role_id = role_id
        phase.user_id = int(user_id) if user_id else None
        phase.skill = skill
        
        db_session.add(phase)
        db_session.commit()
        return RedirectResponse(f'/projects/{project_id}', status_code=303)

@rt('/')
def index():
    return RedirectResponse('/dashboard', status_code=303)

if __name__ == '__main__':
    serve()
