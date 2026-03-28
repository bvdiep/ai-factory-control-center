import os
import json
from datetime import datetime
from sqlmodel import Session
from app.core.database import engine
from app.models import Execution, ExecutionMessage
from app.core.config import settings

from openhands.sdk.agent import Agent
from openhands.sdk.llm import LLM
from openhands.sdk.conversation import LocalConversation
from openhands.sdk.workspace import LocalWorkspace
from openhands.sdk.event import Event, MessageEvent, ActionEvent, ObservationEvent
from openhands.sdk.tool import Tool
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.browser_use import BrowserToolSet

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

def run_agent_in_background(project_id, phase_id, execution_id, model_name, prompt, project_path, skill):
    import sys as _sys

    # Setup Log File early so stdout redirect can start immediately
    log_dir = os.path.join(settings.OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"{execution_id}.log")

    old_stdout = _sys.stdout
    writer = _FileWriter(log_file_path)
    _sys.stdout = writer

    try:
        # Setup LLM
        api_key = settings.OPENAI_API_KEY if "gpt" in model_name else settings.GEMINI_API_KEY
        llm = LLM(model=model_name, api_key=api_key)

        # Setup Workspace
        workspace = LocalWorkspace(working_dir=project_path)

        # Setup Agent with tools
        tools = [
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
            Tool(name=BrowserToolSet.name),
        ]
        agent = Agent(llm=llm, tools=tools)

        # Setup Conversation session dir
        session_dir = os.path.join(settings.OPENHANDS_STORAGE_PATH, str(project_id), str(phase_id), "sessions")
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
        if skill:
            prompt = f"System Instruction: {skill}\n\nUser Request: {prompt}"

        conversation.send_message(prompt)

        # Run the agent — all internal SDK prints will be captured
        conversation.run()

        # Save final metrics
        with Session(engine) as db_session:
            execution = db_session.get(Execution, execution_id)
            if execution:
                execution.status = "completed"
                metrics_json = None
                if hasattr(llm, 'metrics') and llm.metrics.accumulated_token_usage:
                    m = llm.metrics
                    tu = m.accumulated_token_usage
                    execution.total_cost = (execution.total_cost or 0) + m.accumulated_cost
                    execution.total_input_tokens = (execution.total_input_tokens or 0) + (tu.prompt_tokens or 0)
                    execution.total_output_tokens = (execution.total_output_tokens or 0) + (tu.completion_tokens or 0)
                    execution.total_reasoning_tokens = (execution.total_reasoning_tokens or 0) + (tu.reasoning_tokens or 0)
                    execution.cache_read_tokens = (execution.cache_read_tokens or 0) + (tu.cache_read_tokens or 0)
                    execution.cache_write_tokens = (execution.cache_write_tokens or 0) + (tu.cache_write_tokens or 0)

                    prompt_tokens = (execution.total_input_tokens or 0)
                    cache_read = (execution.cache_read_tokens or 0)
                    execution.cache_hit_percent = (cache_read / prompt_tokens * 100) if prompt_tokens > 0 else 0.0

                    if m.response_latencies:
                        execution.latency = m.response_latencies[-1].latency

                    if tu.model:
                        execution.model_name = tu.model

                    metrics_dict = {
                        "prompt_tokens": tu.prompt_tokens,
                        "completion_tokens": tu.completion_tokens,
                        "reasoning_tokens": tu.reasoning_tokens,
                        "cache_read_tokens": tu.cache_read_tokens,
                        "cache_write_tokens": tu.cache_write_tokens,
                        "cache_hit_percent": execution.cache_hit_percent,
                        "latency": execution.latency,
                        "model_name": execution.model_name,
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
