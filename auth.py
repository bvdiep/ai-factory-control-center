from passlib.context import CryptContext
from sqlmodel import Session, select
from models import User
from database import engine
from fasthtml.common import RedirectResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username, password):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user

def auth_beforeware(req, session):
    auth = session.get('user_id', None)
    if not auth and req.url.path not in ['/login', '/static', '/favicon.ico']:
        return RedirectResponse('/login', status_code=303)
