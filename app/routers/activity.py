from fasthtml.common import *
from sqlmodel import Session, select
from app.core.database import engine
from app.models import User, Project, Phase

def setup_activity_routes(rt, render_nav):
    @rt('/my-activity')
    def my_activity(session):
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            if not user: return RedirectResponse('/login', status_code=303)
            
            # Get projects where user is assigned to at least one phase
            # Sort by created_at desc of project
            projects = db_session.exec(
                select(Project)
                .join(Phase)
                .where(Phase.user_id == user_id)
                .distinct()
                .order_by(Project.created_at.desc())
            ).all()
            
            project_sections = []
            for project in projects:
                # Get all phases for this project, ordered by order
                phases = db_session.exec(
                    select(Phase)
                    .where(Phase.project_id == project.id)
                    .order_by(Phase.order)
                ).all()
                
                phase_cards = []
                for p in phases:
                    is_assigned_to_me = p.user_id == user_id
                    card_cls = "phase-card assigned" if is_assigned_to_me else "phase-card unassigned"
                    
                    execute_button = A(Button("Execute", 
                                          cls="small outline",
                                          style="margin-bottom: 0;"),
                                      href=f"/projects/{p.project_id}/phases/{p.id}/execution") if is_assigned_to_me else ""
                    
                    phase_cards.append(Div(
                        Div(
                            Span(str(p.order), cls="phase-order"),
                            Span(p.status, cls="phase-status"),
                            cls="phase-badge"
                        ),
                        P(p.mission, cls="phase-mission"),
                        Div(
                            Div(
                                Span("👤", style="font-size: 0.8rem;"),
                                Span(p.user.username if p.user else "Unassigned"),
                                cls="phase-user"
                            ),
                            execute_button,
                            cls="phase-footer"
                        ),
                        cls=card_cls
                    ))
                
                project_sections.append(Section(
                    H3(project.name, style="margin-bottom: 1rem; border-left: 4px solid var(--pico-secondary); padding-left: 0.5rem;"),
                    Div(*phase_cards, cls="phase-grid"),
                    style="margin-bottom: 3rem;"
                ))
            
            return Title("My Activity"), render_nav(user), Main(
                H1("My Activity", style="margin-bottom: 2rem;"),
                *project_sections if project_sections else P("No activities found."),
                cls="container"
            )
