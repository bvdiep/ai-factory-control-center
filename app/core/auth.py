import bcrypt
from sqlmodel import Session, select
from app.models import User
from app.core.database import engine
from fasthtml.common import RedirectResponse

def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
