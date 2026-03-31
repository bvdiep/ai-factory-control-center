import os
from sqlmodel import SQLModel, create_engine, Session, select
from app.core.config import settings
from app.models import Role, User, Project, Phase, Execution, ExecutionMessage

# SQLite connection
sqlite_file_name = settings.DB_PATH
sqlite_url = f"sqlite:///{sqlite_file_name}"
sqlite_engine = create_engine(sqlite_url)

# MySQL connection
mysql_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
mysql_engine = create_engine(mysql_url)

def migrate_data():
    # Create tables in MySQL
    SQLModel.metadata.create_all(mysql_engine)

    with Session(sqlite_engine) as sqlite_session:
        with Session(mysql_engine) as mysql_session:
            # Migrate Role
            roles = sqlite_session.exec(select(Role)).all()
            for role in roles:
                mysql_session.add(Role(**role.dict()))
            mysql_session.commit()

            # Migrate User
            users = sqlite_session.exec(select(User)).all()
            for user in users:
                mysql_session.add(User(**user.dict()))
            mysql_session.commit()

            # Migrate Project
            projects = sqlite_session.exec(select(Project)).all()
            for project in projects:
                mysql_session.add(Project(**project.dict()))
            mysql_session.commit()

            # Migrate Phase
            phases = sqlite_session.exec(select(Phase)).all()
            for phase in phases:
                mysql_session.add(Phase(**phase.dict()))
            mysql_session.commit()

            # Migrate Execution
            executions = sqlite_session.exec(select(Execution)).all()
            for execution in executions:
                mysql_session.add(Execution(**execution.dict()))
            mysql_session.commit()

            # Migrate ExecutionMessage
            messages = sqlite_session.exec(select(ExecutionMessage)).all()
            for message in messages:
                mysql_session.add(ExecutionMessage(**message.dict()))
            mysql_session.commit()

    print("Data migration completed successfully.")

if __name__ == "__main__":
    migrate_data()