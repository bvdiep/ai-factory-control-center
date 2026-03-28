import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, text
from app.core.database import engine, create_db_and_tables
from app.models import Role, User, Project
from app.core.auth import get_password_hash

def migrate_execution_add_project_id():
    """Add project_id column to execution table and backfill from phase."""
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(execution)"))
        columns = [row[1] for row in result.fetchall()]
        if 'project_id' in columns:
            print("Column 'project_id' already exists in execution table.")
            return

        print("Adding project_id column to execution table...")
        # Add column with default value first (SQLite requires a default for NOT NULL add)
        conn.execute(text("ALTER TABLE execution ADD COLUMN project_id INTEGER"))
        conn.commit()

        # Backfill project_id from phase table
        conn.execute(text(
            "UPDATE execution SET project_id = ("
            "  SELECT phase.project_id FROM phase WHERE phase.id = execution.phase_id"
            ")"
        ))
        conn.commit()

        print("Backfilled project_id for existing execution records.")

def seed_db():
    create_db_and_tables()
    migrate_execution_add_project_id()
    
    with Session(engine) as session:
        # Check if already seeded
        if session.exec(select(Role)).first():
            print("Database already seeded.")
            return

        # Create Roles
        roles_data = [
            "Admin", "Senior", "Junior", "DevOps", "BA", "QC", "QA", "CEO", "Account", "PM"
        ]
        roles = {}
        for r_name in roles_data:
            role = Role(name=r_name, skill=f"You are a {r_name}.")
            session.add(role)
            roles[r_name] = role
        
        session.commit()
        
        # Create Admin User
        admin_role = session.exec(select(Role).where(Role.name == "Admin")).first()
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role_id=admin_role.id
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        # Create Projects
        p1 = Project(
            name="AI Factory",
            description="Main control center",
            path="ai-factory-control-center",
            user_id=admin_user.id
        )
        p2 = Project(
            name="Data Pipeline",
            description="ETL pipeline for AI models",
            path="data-pipeline",
            user_id=admin_user.id
        )
        session.add(p1)
        session.add(p2)
        session.commit()
        session.refresh(p1)
        session.refresh(p2)
        
        print("Database seeded successfully.")

if __name__ == "__main__":
    seed_db()
