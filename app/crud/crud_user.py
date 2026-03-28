from sqlmodel import Session, select
from app.models import User

def get_user_by_id(db_session: Session, user_id: int):
    return db_session.get(User, user_id)

def get_user_by_username(db_session: Session, username: str):
    return db_session.exec(select(User).where(User.username == username)).first()

def get_all_users(db_session: Session):
    return db_session.exec(select(User)).all()
