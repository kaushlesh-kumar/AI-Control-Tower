from models import User, Token, TokenPolicy
from auth import hash_password, create_access_token
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

def create_user(db: Session, name: str, email: str, password: str):
    user = User(name=name, email=email, hashed_password=hash_password(password), created_at=datetime.utcnow())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_token(db: Session, user_id: int, description="", expires_at=None):
    print(f"create_token: expires_at={expires_at} (type={type(expires_at)})")
    if expires_at:
        expires_delta = expires_at - datetime.utcnow()
        print(f"create_token: expires_delta={expires_delta}")
        if expires_delta.total_seconds() <= 0:
            raise ValueError("expires_at must be in the future")
    else:
        expires_delta = None
    # Convert user_id to string for the JWT 'sub' claim
    token_str = create_access_token({"sub": str(user_id)}, expires_delta=expires_delta)
    token = Token(token=token_str, user_id=user_id, description=description, expires_at=expires_at)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token

def add_policy(db: Session, token_id:int, model_name: str, rate_limit: int, quota: int = None):
    policy = TokenPolicy(token_id=token_id, model_name=model_name,
                         rate_limit_per_minute=rate_limit, monthly_quota_tokens=quota)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

def get_all_users(db):
    return db.query(User).all()

def get_tokens_for_user(db: Session, user_id: int):
    return db.query(Token).filter(Token.user_id == user_id).all()