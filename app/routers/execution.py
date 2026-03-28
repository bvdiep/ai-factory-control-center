import os
import json
import asyncio
import html
from datetime import datetime
from fasthtml.common import *
from sqlmodel import Session, select
from app.core.database import engine
from app.models import User, Project, Phase, Execution, ExecutionMessage
from dotenv import load_dotenv

from openhands.sdk.agent import Agent
from openhands.sdk.llm import LLM
from openhands.sdk.conversation import LocalConversation
from openhands.sdk.workspace import LocalWorkspace
from openhands.sdk.event import Event, MessageEvent, ActionEvent, ObservationEvent

load_dotenv()

OPENHANDS_STORAGE_PATH = os.getenv("OPENHANDS_STORAGE_PATH", "./storage")

class _FileWriter:
    """Redirect sys.stdout to a log file so all SDK print() output is captured."""
    def __init__(self, path):
        self._f = open(path, "a", encoding="utf-8")

    def write(self, data):
        if data:
            self._f.write(data)
            self._f.flush()

    def flush(self):
        self._f.flush()

    def close(self):
        self._f.close()

    @property
    def encoding(self):
        import sys
        return getattr(sys.__stdout__, "encoding", "utf-8")


def run_agent_in_background(project_id, phase_id, execution_id, model_name, prompt, project_path, system_prompt):
    import sys as _sys

    # Setup Log File early so stdout redirect can start immediately
    log_dir = os.path.join(OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"{execution_id}.log")

    old_stdout = _sys.stdout
    writer = _FileWriter(log_file_path)
    _sys.stdout = writer

    try:
        # Setup LLM
        api_key = os.getenv("OPENAI_API_KEY") if "gpt" in model_name else os.getenv("GEMINI_API_KEY")
        llm = LLM(model=model_name, api_key=api_key)

        # Setup Agent
        agent = Agent(llm=llm)

        # Setup Workspace
        workspace = LocalWorkspace(working_dir=project_path)

        # Setup Conversation session dir
        session_dir = os.path.join(OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "sessions")
        os.makedirs(session_dir, exist_ok=True)

        agent_messages = []

        def on_event(event: Event):
            try:
                timestamp = datetime.utcnow().isoformat()
                event_type = event.__class__.__name__

                content = ""
                if isinstance(event, MessageEvent):
                    content = str(getattr(event, 'llm_message', getattr(event, 'message', '')))
                    if getattr(event, 'source', '') == 'agent':
                        llm_msg = getattr(event, 'llm_message', None)
                        if llm_msg and getattr(llm_msg, 'role', '') == 'assistant':
                            msg_content = getattr(llm_msg, 'content', [])
                            text_parts = [
                                getattr(part, 'text', '')
                                for part in msg_content
                                if getattr(part, 'type', '') == 'text'
                            ]
                            if text_parts:
                                agent_messages.append("".join(text_parts))
                elif isinstance(event, ActionEvent):
                    action = getattr(event, 'action', None)
                    content = f"Action: {action}"
                    thought = getattr(event, 'thought', '')
                    if thought:
                        content += f" | Thought: {thought}"
                    if action and type(action).__name__ == 'FinishAction':
                        msg = getattr(action, 'message', '')
                        if msg:
                            agent_messages.append(msg)
                elif isinstance(event, ObservationEvent):
                    content = f"Observation: {getattr(event, 'observation', '')}"
                    obs_content = getattr(event, 'content', '')
                    if obs_content:
                        content += f" | Content: {obs_content}"
                else:
                    content = str(event)

                # Write via redirected stdout so it lands in the log file
                print(f"[{timestamp}] [{event_type}] {content}")
            except Exception as ex:
                print(f"[{datetime.utcnow().isoformat()}] [LogError] Failed to log event: {ex}")

        conversation = LocalConversation(
            agent=agent,
            workspace=workspace,
            persistence_dir=session_dir,
            callbacks=[on_event]
        )

        # Send initial prompt
        if system_prompt:
            prompt = f"System Instruction: {system_prompt}\n\nUser Request: {prompt}"

        conversation.send_message(prompt)

        # Run the agent — all internal SDK prints will be captured
        conversation.run()

        # Save final metrics
        with Session(engine) as db_session:
            execution = db_session.get(Execution, execution_id)
            if execution:
                execution.status = "completed"
                metrics_json = None
                if hasattr(llm, 'metrics'):
                    m = llm.metrics
                    execution.total_cost = m.accumulated_cost
                    execution.total_input_tokens = m.accumulated_token_usage.prompt_tokens
                    execution.total_output_tokens = m.accumulated_token_usage.completion_tokens
                    execution.total_reasoning_tokens = m.accumulated_token_usage.reasoning_tokens

                    metrics_dict = {
                        "prompt_tokens": m.accumulated_token_usage.prompt_tokens,
                        "completion_tokens": m.accumulated_token_usage.completion_tokens,
                        "reasoning_tokens": m.accumulated_token_usage.reasoning_tokens,
                        "cost": m.accumulated_cost
                    }
                    metrics_json = json.dumps(metrics_dict)

                if agent_messages:
                    agent_msg = ExecutionMessage(
                        execution_id=execution.id,
                        role="agent",
                        content=agent_messages[-1],
                        metrics=metrics_json
                    )
                    db_session.add(agent_msg)

                db_session.add(execution)
                db_session.commit()

    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] [Error] {e}")
        import traceback
        traceback.print_exc()

        with Session(engine) as db_session:
            execution = db_session.get(Execution, execution_id)
            if execution:
                execution.status = "failed"
                db_session.add(execution)
                db_session.commit()

    finally:
        _sys.stdout = old_stdout
        writer.close()

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

            session_dir = os.path.join(OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "sessions")
            log_dir = os.path.join(OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "logs")
            os.makedirs(session_dir, exist_ok=True)
            os.makedirs(log_dir, exist_ok=True)

            execution = db_session.exec(
                select(Execution).where(Execution.phase_id == phase_id).order_by(Execution.id.desc())
            ).first()

            if not execution:
                execution = Execution(phase_id=phase_id)
                db_session.add(execution)
                db_session.commit()
                db_session.refresh(execution)

            header_card = Article(
                Grid(
                    Div(Strong("Project: "), project.name),
                    Div(Strong("Workspace: "), project.path),
                    Div(Strong("Status: "), phase.status)
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
                Label("Model", Select(
                    Option("openai-gpt-4o-mini", value="openai/gpt-4o-mini"),
                    Option("gemini-3-flash-preview", value="gemini/gemini-3-flash-preview"),
                    name="model"
                )),
                Label("Prompt", Textarea(name="prompt", rows=5, placeholder="Enter your prompt here...")),
                Button("Execute", type="submit", style="margin-top: 1rem;"),
                hx_post=f"/projects/{project_id}/phases/{phase_id}/execute",
                hx_target="#log-container",
                hx_swap="beforeend"
            )

            log_display = Div(
                H4("Logs", style="margin-top: 2rem;"),
                Div(
                    Pre(id="log-container", cls="console-log", style="white-space: pre-wrap;"),
                ),
                Script(f"""
                    (function() {{
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

            return Title(f"Execute Phase - {project.name}"), render_nav(user), Main(
                H1("Execution"),
                header_card,
                mission_card,
                execution_form,
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
            log_file = os.path.join(OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "logs", f"{execution_id}.log")

            if not os.path.exists(log_file):
                with open(log_file, 'w', encoding="utf-8") as f:
                    f.write(f"[{datetime.utcnow().isoformat()}] Log started\n")

            with open(log_file, 'r', encoding="utf-8") as f:
                for line in f:
                    yield f"data: <span>{html.escape(line)}</span>\n\n"

                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.5)
                        continue
                    yield f"data: <span>{html.escape(line)}</span>\n\n"

        from starlette.responses import StreamingResponse
        return StreamingResponse(log_generator(), media_type="text/event-stream", headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})
