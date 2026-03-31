import sys
import os
import json

from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fasthtml.common import *
from sqlmodel import Session, select
from app.core.database import engine
from app.models import User, Project, Role, Phase, Execution
from app.core.auth import authenticate_user, auth_beforeware
from app.routers.users import setup_user_routes
from app.routers.projects import setup_project_routes
from app.routers.activity import setup_activity_routes
from app.routers.execution import setup_execution_routes
from app.routers.roles import setup_role_routes
from app.routers.files import setup_file_routes
from app.routers.api import setup_api_routes

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
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .dashboard-card {
        padding: 1.25rem;
        border-radius: var(--pico-border-radius);
        border: 1px solid var(--pico-muted-border-color);
        display: flex;
        flex-direction: column;
        height: 200px;
        overflow: hidden;
        transition: transform 0.2s;
    }
    .dashboard-card:hover {
        transform: translateY(-4px);
    }
    .dashboard-card-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .dashboard-card-desc {
        flex-grow: 1;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        font-size: 0.9rem;
        color: var(--pico-muted-color);
    }
    .dashboard-card-footer {
        margin-top: auto;
        font-size: 0.8rem;
        color: var(--pico-muted-color);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .project-card {
        background-color: rgba(41, 128, 185, 0.05);
        border-color: rgba(41, 128, 185, 0.2);
    }
    .activity-card {
        background-color: rgba(39, 174, 96, 0.05);
        border-color: rgba(39, 174, 96, 0.2);
    }
    @media (max-width: 1024px) {
        .dashboard-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (max-width: 768px) {
        .dashboard-grid {
            grid-template-columns: 1fr;
        }
    }
    .phase-grid {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .phase-card {
        padding: 1.25rem;
        border-radius: var(--pico-border-radius);
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        display: flex;
        flex-direction: column;
        gap: 1rem;
        position: relative;
        transition: transform 0.2s;
    }
    .phase-card:hover {
        transform: translateY(-4px);
    }
    .phase-card.assigned {
        border: 1px solid var(--pico-primary);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    .phase-card.unassigned {
        opacity: 0.6;
        filter: grayscale(0.5);
    }
    .phase-badge {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .phase-order {
        background: var(--pico-primary);
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .phase-status {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        background: var(--pico-muted-background-color);
    }
    .phase-mission {
        font-size: 0.95rem;
        line-height: 1.5;
        flex-grow: 1;
        margin: 0;
    }
    .phase-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid var(--pico-muted-border-color);
        padding-top: 0.75rem;
        margin-top: 0.5rem;
    }
    .phase-user {
        font-size: 0.85rem;
        color: var(--pico-secondary);
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .console-log {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 4px;
        min-height: 200px;
        max-height: 500px;
        overflow-y: auto;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.9rem;
        line-height: 1.4;
        border: 1px solid #333;
    }
    .management-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .management-card {
        padding: 1.25rem;
        border-radius: var(--pico-border-radius);
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        position: relative;
    }
    .management-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.5rem;
    }
    .management-card-title {
        font-weight: bold;
        font-size: 1.1rem;
        margin: 0;
    }
    .management-card-content {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 0.5rem 1.5rem;
        font-size: 0.9rem;
    }
    .management-card-item {
        display: flex;
        flex-direction: column;
    }
    .management-card-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: var(--pico-muted-color);
        font-weight: 600;
    }
    .management-card-actions {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 1.5rem;
        border-top: 1px solid var(--pico-muted-border-color);
        padding-top: 0.75rem;
        margin-top: 0.5rem;
    }
    @media (max-width: 600px) {
        .management-card-actions {
            flex-direction: column;
            align-items: stretch;
            gap: 0.5rem;
        }
        .management-card-actions > * {
            width: 100%;
            text-align: center;
        }
    }
''')

from app.core.config import settings

app, rt = fast_app(
    hdrs=(css, Script(src="https://unpkg.com/htmx.org@1.9.12/dist/ext/sse.js")),
    before=Beforeware(auth_beforeware, skip=['/login', '/static', '/favicon.ico', '/api/projects']),
    secret_key=settings.SECRET_KEY,
    static_path="app/static"
)

def render_nav(user=None):
    nav_items = [Li(A("Home", href="/dashboard", cls="secondary"))]
    if user:
        nav_items.append(Li(A("My Activity", href="/my-activity", cls="secondary")))
    if user and user.role and user.role.name == 'Admin':
        nav_items.append(Li(A("Projects", href="/projects", cls="secondary")))
        nav_items.append(Li(A("Users", href="/users", cls="secondary")))
        nav_items.append(Li(A("Role-Skill", href="/roles", cls="secondary")))
    nav_items.append(Li(A("Logout", href="/logout", cls="secondary")))
    
    return Nav(
        Ul(Li(A(Strong("AI Factory"), href="/dashboard", cls="secondary"))),
        Ul(*nav_items),
        cls="container"
    )

setup_user_routes(rt, render_nav)
setup_project_routes(rt, render_nav)
setup_activity_routes(rt, render_nav)
setup_execution_routes(rt, render_nav)
setup_role_routes(rt, render_nav)
setup_file_routes(rt, render_nav)
setup_api_routes(rt)
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

        project_cards = Div(
            *[A(
                Div(
                    Div(p.name, cls="dashboard-card-title"),
                    Div(p.description or "No description", cls="dashboard-card-desc"),
                    Div(f"Path: {p.path}", cls="dashboard-card-footer"),
                    cls="dashboard-card project-card"
                ),
                href=f"/projects/{p.id}",
                style="text-decoration: none; color: inherit;"
            ) for p in projects],
            cls="dashboard-grid"
        ) if projects else P("No projects assigned.")

        assigned_phases = db_session.exec(
            select(Phase).where(Phase.user_id == user.id).order_by(Phase.updated_at.desc())
        ).all()

        activity_cards = Div(
            *[A(
                Div(
                    Div(
                        Span(f"Phase {ph.order}: {ph.project.name}", cls="dashboard-card-title"),
                        Span(ph.status.upper(), cls=f"phase-status status-{ph.status.lower()}", style="float: right; font-size: 0.7rem; font-weight: bold; padding: 0.2rem 0.5rem; border-radius: 4px; background-color: var(--pico-primary-background); color: var(--pico-primary-inverse);"),
                    ),
                    Div(ph.mission or "No mission", cls="dashboard-card-desc", style="margin-top: 0.5rem;"),
                    Div(f"Updated: {ph.updated_at.strftime('%Y-%m-%d %H:%M')}", cls="dashboard-card-footer"),
                    cls="dashboard-card activity-card"
                ),
                href=f"/projects/{ph.project_id}/phases/{ph.id}/execution",
                style="text-decoration: none; color: inherit;"
            ) for ph in assigned_phases],
            cls="dashboard-grid"
        ) if assigned_phases else P("No recent activity.")

        return Title("Dashboard"), render_nav(user), Main(
            H1("Dashboard"),
            Div(
                H2(f"{user.name}"),
                P(f"Your Role: {role.name if role else 'None'}"),
                P("- Admin: tạo ra các project, gán project cho PM."),
                P("- PM: Phân chia project thành các phases. Không cần phải có tất cả các phase ngay từ đầu. Phase mới sinh ra sẽ ở trạng thái Pending, không member nào được can thiệp."),
                P("- PM kích hoạt một phase để member có thể làm bằng cách chuyển status của nó sang Start."),
                P("- Khi được kích hoạt thì member mới được thao tác: member làm việc với Agent AI để hoàn thành công việc của mình. Status của phase là Processing. Member chuyển thành Processed khi kết thúc."),
                P("- PM sẽ review để Approve (chuyển status thành Done)"),
                Hr(),
                H3("Your Projects"),
                project_cards,
                Hr(),
                H3("Activity"),
                activity_cards
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
        is_pm = project.user_id == user.id
        
        # Also allow access if user is assigned to any phase in the project
        user_assigned_to_any_phase = db_session.exec(
            select(Phase).where(Phase.project_id == id, Phase.user_id == user_id)
        ).first() is not None

        if not (is_admin or is_pm or user_assigned_to_any_phase):
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
            Td(A("Edit", href=f"/projects/{id}/phases/{p.id}/edit", cls="button") if p.status == 'Pending' else "")
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
                P(Strong("Interview Minutes: "), project.interview_minutes),
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
def add_phase(project_id: int, order: int, mission: str, role_id: int = None, user_id: str = None, session = None):
    with Session(engine) as db_session:
        # Check order constraint
        next_phase = db_session.exec(
            select(Phase)
            .where(Phase.project_id == project_id)
            .where(Phase.order > order)
            .order_by(Phase.order)
        ).first()
        
        if next_phase and next_phase.status != 'Pending':
            return Title("Error"), Main(H1("Error"), P("Cannot add phase before a phase that is already started/done."), A("Back", href=f"/projects/{project_id}"))

        new_phase = Phase(
            project_id=project_id,
            order=order,
            mission=mission,
            role_id=role_id,
            user_id=int(user_id) if user_id else None,
            skill=None,
            status="Pending"
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
        
        executions = db_session.exec(
            select(Execution).where(Execution.phase_id == phase_id, Execution.project_id == project_id)
        ).all()

        total_input = sum(e.total_input_tokens for e in executions if e.total_input_tokens)
        total_output = sum(e.total_output_tokens for e in executions if e.total_output_tokens)
        total_reasoning = sum(e.total_reasoning_tokens for e in executions if e.total_reasoning_tokens)
        total_cost = sum(e.total_cost for e in executions if e.total_cost)
        total_cache_read = sum(e.cache_read_tokens for e in executions if e.cache_read_tokens)
        cache_hit_list = [e.cache_hit_percent for e in executions if e.cache_hit_percent > 0]
        avg_cache_hit = sum(cache_hit_list) / len(cache_hit_list) if cache_hit_list else 0.0
        latency_list = [e.latency for e in executions if e.latency > 0]
        avg_latency = sum(latency_list) / len(latency_list) if latency_list else 0.0

        metrics_bar = Grid(
            Div(Small(Span("Token In: ", style="color: #666;"), Strong(f"{total_input:,}")), style="background: #f0f4f8; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Token Out: ", style="color: #666;"), Strong(f"{total_output:,}")), style="background: #fffbeb; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Reasoning: ", style="color: #666;"), Strong(f"{total_reasoning:,}")), style="background: #f5f3ff; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Cache Read: ", style="color: #666;"), Strong(f"{total_cache_read:,}")), style="background: #fdf2f8; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Cache Hit: ", style="color: #666;"), Strong(f"{avg_cache_hit:.2f}%")), style="background: #f0fdf4; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Avg Latency: ", style="color: #666;"), Strong(f"{avg_latency:.2f}s")), style="background: #fef3c7; padding: 0.5rem; border-radius: 8px; text-align: center;"),
            Div(Small(Span("Total Cost: ", style="color: #666;"), Strong(f"${total_cost:.4f}")), style="background: #fee2e2; padding: 0.5rem; border-radius: 8px; text-align: center;"),
        )
        
        next_status = 'Start' if phase.status == 'Pending' else 'Pending'
        approve_status = 'Done' if phase.status == 'Processed' else 'Processed'
        
        project_phase_info = Article(
            Grid(
                Div(
                    H4("Project"),
                    P(Strong("Name: "), project.name if project else "N/A"),
                    P(Strong("Description: "), (project.description or "N/A") if project else "N/A"),
                    P(Strong("Interview Minutes: "), (project.interview_minutes or "N/A") if project else "N/A"),
                    P(Strong("Path: "), project.path if project else "N/A"),
                    P(Strong("Status: "), project.status if project else "N/A"),
                ),
                Div(
                    H4("Phase Info"),
                    P(Strong("Role: "), phase.role.name if phase.role else "N/A"),
                    P(Strong("User: "), phase.user.username if phase.user else "Unassigned"),
                    P(
                        Label(phase.status, style=f"background: {'#22c55e' if phase.status == 'Processed' else '#10b981' if phase.status == 'Done' else '#3b82f6' if phase.status == 'Processing' else '#eab308' if phase.status == 'Start' else '#ef4444' if phase.status == 'Cancel' else '#6b7280'}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 1rem;"),
                        A("Execute →", href=f"/projects/{project.id}/phases/{phase.id}/execution", style="float: right; text-decoration: underline;") if user.id == phase.user_id else None
                    ),
                    Div(
                        # PM buttons
                        Group(
                            Button("Cancel", 
                                   hx_post=f"/projects/{project_id}/phases/{phase_id}/status",
                                   hx_vals=json.dumps({"status": "Cancel"}),
                                   hx_confirm="Are you sure you want to cancel this phase?",
                                   cls="outline", 
                                   disabled=phase.status == 'Cancel'),
                            Button("Approve" if phase.status != 'Done' else "Unapprove", 
                                   hx_post=f"/projects/{project_id}/phases/{phase_id}/status",
                                   hx_vals=json.dumps({"status": approve_status}),
                                   cls="outline", 
                                   disabled=phase.status not in ['Processed', 'Done']),
                            Button("Pending" if phase.status == 'Start' else "Start", 
                                   hx_post=f"/projects/{project_id}/phases/{phase_id}/status",
                                   hx_vals=json.dumps({"status": next_status}),
                                   cls="outline", 
                                   disabled=phase.status not in ['Pending', 'Start']),
                        ) if user.id == project.user_id else None,
                        style="margin-top: 1rem;"
                    ) if user.id == project.user_id else None
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
                P(phase.role.skill if phase.role and phase.role.skill else "No skills defined"),
                H2("Conversation"),
                A("View Conversation", href="#",
                  hx_get=f"/projects/{project_id}/phases/{phase_id}/conversation/{executions[0].id}" if executions else "#",
                  hx_target="#conversation-content-container",
                  hx_swap="innerHTML",
                  onclick="document.getElementById('conversation-modal').showModal(); return false;" if executions else "alert('No executions yet'); return false;"),
                Footer(A("Back to Project", href=f"/projects/{project_id}", cls="button"))
            ),
            cls="container"
        ), Dialog(
                Article(
                    Header(H3("Conversation")),
                    Div(
                        P("Click Conversation button to load messages.", style="color: #666; font-style: italic;"),
                        id="conversation-content-container",
                        style="max-height: 500px; overflow-y: auto;"
                    ),
                    Footer(
                        Button("Close", onclick="document.getElementById('conversation-modal').close()", type="button")
                    )
                ),
                id="conversation-modal",
                style="max-width: 90vw; width: 90vw; max-height: 80vh;",
                onopen="setTimeout(() => { const c = document.getElementById('conversation-content-container'); if(c) c.scrollTop = c.scrollHeight; }, 50)"
            ),


@rt('/projects/{project_id}/phases/{phase_id}/status', methods=['POST'])
async def update_phase_status(project_id: int, phase_id: int, session, status: str = None, req=None):
    user_id = session.get('user_id')
    if not user_id:
        return Response(status_code=401)

    if not status and req:
        try:
            data = await req.json()
            status = data.get('status')
        except:
            pass
    
    # Check if status is in form data (HTMX default)
    if not status and req:
        try:
            form = await req.form()
            status = form.get('status')
        except:
            pass

    if not status:
        return Response(status_code=400)

    with Session(engine) as db_session:
        project = db_session.get(Project, project_id)
        if not project or project.user_id != user_id:
            return Response(status_code=403)

        phase = db_session.get(Phase, phase_id)
        if not phase or phase.project_id != project_id:
            return Response(status_code=404)

        phase.status = status
        db_session.add(phase)
        db_session.commit()

        return Response(content="", headers={"HX-Refresh": "true"})

@rt('/projects/{project_id}/phases/{phase_id}/edit', methods=['GET'])
def edit_phase_get(project_id: int, phase_id: int, session):
    user_id = session.get('user_id')
    with Session(engine) as db_session:
        user = db_session.get(User, user_id)
        phase = db_session.get(Phase, phase_id)
        if not phase or phase.status != 'Pending':
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
def edit_phase_post(project_id: int, phase_id: int, order: int, mission: str, role_id: int = None, user_id: str = None, skill: str = None, session = None):
    with Session(engine) as db_session:
        phase = db_session.get(Phase, phase_id)
        if not phase or phase.status != 'Pending':
            return RedirectResponse(f'/projects/{project_id}', status_code=303)
        
        phase.order = order
        phase.mission = mission
        phase.role_id = role_id
        phase.user_id = int(user_id) if user_id else None
        phase.skill = skill
        phase.updated_at = datetime.utcnow()
        
        db_session.add(phase)
        db_session.commit()
        return RedirectResponse(f'/projects/{project_id}', status_code=303)

@rt('/')
def index():
    return RedirectResponse('/dashboard', status_code=303)

if __name__ == '__main__':
    is_prod = os.environ.get('NODE_ENV') == 'production'
    serve(port=5001, reload=not is_prod, reload_excludes=['*.log', '*.db', '*.db-journal', 'logs/*', 'logs/**/*'])
