from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Text
from datetime import datetime

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    skill: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    users: List["User"] = Relationship(back_populates="role")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    name: Optional[str] = None
    hashed_password: str
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    role: Optional[Role] = Relationship(back_populates="users")
    projects: List["Project"] = Relationship(back_populates="user")

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    interview_minutes: Optional[str] = None
    path: str = Field(unique=True, index=True)
    config_override: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    user: Optional[User] = Relationship(back_populates="projects")
    phases: List["Phase"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    executions: List["Execution"] = Relationship(back_populates="project")

class Phase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mission: str = Field(nullable=False)
    project_id: int = Field(foreign_key="project.id", nullable=False)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    skill: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: str = Field(default="Pending") # Pending, Start, Processing, Processed, Cancel, Done
    logging: Optional[str] = Field(default=None, sa_column=Column(Text))
    token_in: int = Field(default=0)
    token_out: int = Field(default=0)
    cache_hit: float = Field(default=0.0)
    reasoning: int = Field(default=0)
    order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Project = Relationship(back_populates="phases")
    role: Optional[Role] = Relationship()
    user: Optional[User] = Relationship()
    executions: List["Execution"] = Relationship(back_populates="phase", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Execution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phase_id: int = Field(foreign_key="phase.id", nullable=False)
    project_id: int = Field(foreign_key="project.id", nullable=False)
    status: str = Field(default="Pending")
    start_date: datetime = Field(default_factory=datetime.utcnow)
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    total_reasoning_tokens: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    cache_read_tokens: int = Field(default=0)
    cache_write_tokens: int = Field(default=0)
    cache_hit_percent: float = Field(default=0.0)
    latency: float = Field(default=0.0)
    model_name: Optional[str] = Field(default=None)

    phase: Phase = Relationship()
    project: Project = Relationship(back_populates="executions")
    messages: List["ExecutionMessage"] = Relationship(back_populates="execution", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class ExecutionMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    execution_id: int = Field(foreign_key="execution.id", nullable=False)
    role: str = Field(nullable=False)
    content: str = Field(sa_column=Column(Text, nullable=False))
    metrics: Optional[str] = Field(default=None, sa_column=Column(Text)) # JSON string

    execution: Execution = Relationship(back_populates="messages")
