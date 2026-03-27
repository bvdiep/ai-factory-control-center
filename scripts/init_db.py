import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.database import engine, create_db_and_tables
from app.models import Role, User, Project
from app.core.auth import get_password_hash

def seed_db():
    create_db_and_tables()
    
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
            role = Role(name=r_name, system_prompt=f"You are a {r_name}.")
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
            path="/home/dd/work/diep/ai-factory-control-center",
            user_id=admin_user.id
        )
        p2 = Project(
            name="Data Pipeline",
            description="ETL pipeline for AI models",
            path="/home/dd/work/diep/data-pipeline",
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
