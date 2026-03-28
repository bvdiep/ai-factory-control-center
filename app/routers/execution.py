import os
import json
import asyncio
import html
import markdown
from markupsafe import Markup
from datetime import datetime
from fasthtml.common import *
from sqlmodel import Session, select, asc
from app.core.database import engine
from app.models import User, Project, Phase, Execution, ExecutionMessage
from app.core.config import settings
from app.services.openhands_service import run_agent_in_background

def setup_execution_routes(rt, render_nav):
    @rt('/projects/{project_id}/phases/{phase_id}/execution')
    def phase_execution(project_id: int, phase_id: int, session):
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            phase = db_session.get(Phase, phase_id)
            project = db_session.get(Project, project_id)
            if not user or not phase or not project or phase.project_id != project_id:
                return RedirectResponse('/dashboard', status_code=303)

            session_dir = os.path.join(settings.OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "sessions")
            log_dir = os.path.join(settings.OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "logs")
            os.makedirs(session_dir, exist_ok=True)
            os.makedirs(log_dir, exist_ok=True)

            executions = db_session.exec(
                select(Execution).where(Execution.phase_id == phase_id).order_by(Execution.id.desc())
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
                id="metrics-bar"
            )

            execution = executions[0] if executions else None

            if not execution:
                execution = Execution(phase_id=phase_id)
                db_session.add(execution)
                db_session.commit()
                db_session.refresh(execution)

            header_card = Article(
                Grid(
                    Div(Strong("Project: "), project.name, style="flex: 0 0 auto;"),
                    Div(Strong("Workspace: "), project.path, style="flex: 1; min-width: 300px; word-break: break-all;"),
                    Div(
                        Label(phase.status, style=f"background: {'#22c55e' if phase.status == 'completed' else '#3b82f6' if phase.status == 'running' else '#6b7280'}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;")
                    ),
                    style="display: flex; flex-wrap: wrap; gap: 1rem; align-items: center;"
                )
            )

            mission_card = Article(
                Details(
                    Summary(Strong("Mission")),
                    P(phase.mission, style="margin-top: 1rem;")
                ),
                Details(
                    Summary(Strong("System Prompt")),
                    Pre(phase.role.system_prompt if phase.role and phase.role.system_prompt else "No system prompt defined", style="margin-top: 1rem;")
                )
            )

            execution_form = Form(
                Label("Prompt", Textarea(name="prompt", rows=5, placeholder="Enter your prompt here...")),
                Grid(
                    Div(
                        Select(
                            Option("gemini-3-flash-preview", value="gemini/gemini-3-flash-preview"),
                            Option("openai-gpt-5.4-mini", value="openai/gpt-5.4-mini"),
                            name="model"
                        )
                    ),
                    Button("Execute", type="submit", id="execute-btn", style="width: 150px;"),
                    Div(
                        A("Conversation", href="#", onclick="document.getElementById('conversation-modal').showModal(); return false;"),
                        style="text-align: right;"
                    ),
                    style="margin-top: 1rem;"
                ),
                hx_post=f"/projects/{project_id}/phases/{phase_id}/execute",
                hx_target="#log-container",
                hx_swap="beforeend",
                hx_indicator="#execute-btn"
            )

            messages = db_session.exec(
                select(ExecutionMessage).where(ExecutionMessage.execution_id == execution.id).order_by(asc(ExecutionMessage.id))
            ).all()

            message_items = []
            for msg in messages:
                if msg.role == 'user':
                    content = html.escape(msg.content).replace('\n', '<br>')
                else:
                    content = Markup(markdown.markdown(msg.content, extensions=['fenced_code']))
                
                msg_body = Div(
                    Strong(f"{msg.role.upper()}: "),
                    Div(content, style="margin-top: 0.25rem;"),
                )
                
                if msg.metrics:
                    try:
                        m = json.loads(msg.metrics)
                        metrics_info = Div(
                            Small(
                                Span(f"Tokens: {m.get('prompt_tokens', 0)} in / {m.get('completion_tokens', 0)} out | "),
                                Span(f"Cost: ${m.get('cost', 0):.4f} | "),
                                Span(f"Latency: {m.get('latency', 0):.2f}s"),
                                style="color: #666;"
                            ),
                            style="margin-top: 0.5rem;"
                        )
                        msg_body = Div(msg_body, metrics_info)
                    except:
                        pass
                
                msg_div = Div(
                    msg_body,
                    style=f"margin-bottom: 1rem; padding: 0.75rem; border-radius: 8px; background: {'#e0f2fe' if msg.role == 'user' else '#f0fdf4'};"
                )
                message_items.append(msg_div)

            conversation_content = Div(*message_items) if message_items else P("No messages yet.")
            if message_items:
                conversation_content = Div(*message_items, id="conversation-content", style="max-height: 500px; overflow-y: auto;")

            conversation_modal = Dialog(
                Article(
                    Header(H3("Conversation")),
                    conversation_content,
                    Footer(
                        Button("Close", onclick="document.getElementById('conversation-modal').close()", type="button")
                    )
                ),
                id="conversation-modal",
                style="max-width: 90vw; width: 90vw; max-height: 80vh;",
                onopen="setTimeout(() => { const c = document.getElementById('conversation-content'); if(c) c.scrollTop = c.scrollHeight; }, 50)"
            )

            log_display = Div(
                H4("Logs", style="margin-top: 2rem;"),
                Div(
                    Pre(id="log-container", cls="console-log", style="white-space: pre-wrap;"),
                ),
                Script(f"""
                    document.body.addEventListener('htmx:beforeRequest', function(evt) {{
                        const btn = document.getElementById('execute-btn');
                        if (btn) {{
                            btn.disabled = true;
                            btn.dataset.originalText = btn.innerText;
                            btn.innerText = '⏳ Running...';
                        }}
                    }});
                    function checkExecutionStatus() {{
                        fetch('/projects/{project_id}/phases/{phase_id}/execution-status/{execution.id}')
                            .then(r => r.json())
                            .then(data => {{
                                const btn = document.getElementById('execute-btn');
                                if (btn && data.status === 'running') {{
                                    btn.disabled = true;
                                    if (!btn.dataset.originalText) btn.dataset.originalText = btn.innerText;
                                    btn.innerText = '⏳ Running...';
                                }} else if (btn && (data.status === 'completed' || data.status === 'failed')) {{
                                    const promptField = document.querySelector('textarea[name="prompt"]');
                                    btn.disabled = !promptField || promptField.value.trim() === '';
                                    btn.innerText = btn.dataset.originalText || 'Execute';
                                }}
                                if (data.metrics) {{
                                    const metricsBar = document.getElementById('metrics-bar');
                                    if (metricsBar) {{
                                        const m = data.metrics;
                                        const fmt = (n) => typeof n === 'number' ? n.toLocaleString() : '0';
                                        const fmtCost = (n) => typeof n === 'number' ? '$' + n.toFixed(4) : '$0.0000';
                                        const fmtPct = (n) => typeof n === 'number' ? n.toFixed(2) + '%' : '0.00%';
                                        const fmtLat = (n) => typeof n === 'number' ? n.toFixed(2) + 's' : '0.00s';
                                        metricsBar.innerHTML = `
                                            <div style="background: #f0f4f8; padding: 0.5rem; border-radius: 8px; text-align: center;"><small><span style="color: #666;">Token In: </span><strong>${{fmt(m.total_input)}}</strong></small></div>
                                            <div style="background: #fffbeb; padding: 0.5rem; border-radius: 8px; text-align: center;"><small><span style="color: #666;">Token Out: </span><strong>${{fmt(m.total_output)}}</strong></small></div>
                                            <div style="background: #f5f3ff; padding: 0.5rem; border-radius: 8px; text-align: center;"><small><span style="color: #666;">Reasoning: </span><strong>${{fmt(m.total_reasoning)}}</strong></small></div>
                                            <div style="background: #fdf2f8; padding: 0.5rem; border-radius: 8px; text-align: center;"><small><span style="color: #666;">Cache Read: </span><strong>${{fmt(m.total_cache_read)}}</strong></small></div>
                                            <div style="background: #f0fdf4; padding: 0.5rem; border-radius: 8px; text-align: center;"><small><span style="color: #666;">Cache Hit: </span><strong>${{fmtPct(m.avg_cache_hit)}}</strong></small></div>
                                            <div style="background: #fef3c7; padding: 0.5rem; border-radius: 8px; text-align: center;"><small><span style="color: #666;">Avg Latency: </span><strong>${{fmtLat(m.avg_latency)}}</strong></small></div>
                                            <div style="background: #fee2e2; padding: 0.5rem; border-radius: 8px; text-align: center;"><small><span style="color: #666;">Total Cost: </span><strong>${{fmtCost(m.total_cost)}}</strong></small></div>
                                        `;
                                    }}
                                }}
                            }});
                    }}
                    checkExecutionStatus();
                    setInterval(checkExecutionStatus, 2000);
                """),
                Script(f"""
                    (function() {{
                        const promptField = document.querySelector('textarea[name="prompt"]');
                        const btn = document.getElementById('execute-btn');
                        function updateButtonState() {{
                            if (btn) {{
                                btn.disabled = !promptField || promptField.value.trim() === '';
                            }}
                        }}
                        if (promptField) {{
                            promptField.addEventListener('input', updateButtonState);
                            updateButtonState();
                        }}
                        const term = document.getElementById('log-container');
                        const source = new EventSource('/projects/{project_id}/phases/{phase_id}/stream/{execution.id}');
                        source.onmessage = function(event) {{
                            const data = event.data;
                            term.innerHTML += data + '\\n';
                            term.scrollTop = term.scrollHeight;
                        }};
                        source.onerror = function(event) {{
                            source.close();
                        }};
                    }})();
                """)
            )

            extra_css = Style('''
                dialog > article {
                    max-width: 90vw !important;
                    width: 90vw !important;
                }
                dialog > article > * {
                    max-height: 85vh;
                    overflow-y: auto;
                }
            ''')

            return Title(f"Execute Phase - {project.name}"), extra_css, render_nav(user), Main(
                H1("Execution"),
                metrics_bar,
                header_card,
                mission_card,
                execution_form,
                conversation_modal,
                log_display,
                cls="container"
            )

    @rt('/projects/{project_id}/phases/{phase_id}/execute', methods=['POST'])
    async def execute_phase(project_id: int, phase_id: int, model: str, prompt: str, session):
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            phase = db_session.get(Phase, phase_id)
            project = db_session.get(Project, project_id)

            execution = db_session.exec(
                select(Execution).where(Execution.phase_id == phase_id).order_by(Execution.id.desc())
            ).first()

            if not execution:
                return "Execution not found"

            user_msg = ExecutionMessage(
                execution_id=execution.id,
                role="user",
                content=prompt
            )
            db_session.add(user_msg)
            
            execution.status = "running"
            db_session.add(execution)
            db_session.commit()

            system_prompt = phase.role.system_prompt if phase.role else ""
            
            asyncio.create_task(asyncio.to_thread(
                run_agent_in_background,
                project_id,
                phase_id,
                execution.id,
                model,
                prompt,
                project.path,
                system_prompt
            ))

            return Div(f"[{datetime.utcnow().isoformat()}] Started execution with model {model}\n")

    @rt('/projects/{project_id}/phases/{phase_id}/stream/{execution_id}')
    async def stream_logs(project_id: int, phase_id: int, execution_id: int, session):
        async def log_generator():
            log_file = os.path.join(settings.OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "logs", f"{execution_id}.log")

            if not os.path.exists(log_file):
                with open(log_file, 'w', encoding="utf-8") as f:
                    f.write(f"[{datetime.utcnow().isoformat()}] Log started\n")

            with open(log_file, 'r', encoding="utf-8") as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.5)
                        continue
                    yield f"data: <span>{html.escape(line)}</span>\n\n"

        from starlette.responses import StreamingResponse
        return StreamingResponse(log_generator(), media_type="text/event-stream", headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})

    @rt('/projects/{project_id}/phases/{phase_id}/execution-status/{execution_id}')
    async def get_execution_status(project_id: int, phase_id: int, execution_id: int, session):
        with Session(engine) as db_session:
            executions = db_session.exec(
                select(Execution).where(Execution.phase_id == phase_id).order_by(Execution.id.desc())
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
            
            execution = executions[0] if executions else None
            status = execution.status if execution else "unknown"
            
            return {
                "status": status,
                "metrics": {
                    "total_input": total_input,
                    "total_output": total_output,
                    "total_reasoning": total_reasoning,
                    "total_cache_read": total_cache_read,
                    "avg_cache_hit": avg_cache_hit,
                    "avg_latency": avg_latency,
                    "total_cost": total_cost
                }
            }
