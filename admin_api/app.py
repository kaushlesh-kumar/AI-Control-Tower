from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import SessionLocal, Base, engine
from crud import *
from auth import create_access_token, verify_password
from schemas import *

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db,user.name, user.email, user.password)

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.email})
    print(f"Generated token: {token}")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/users/{user_id}/tokens", response_model=TokenOut)
def create_user_token(user_id: int, token: TokenCreate, db: Session = Depends(get_db)):
    return create_token(db, user_id, token.description, token.expires_at)

@app.post("/tokens/{token_id}/policies")
def add_token_policy(token_id: int, policy: PolicyCreate, db: Session = Depends(get_db)):
    return add_policy(db, token_id, policy.model_name, policy.rate_limit_per_minute, policy.monthly_quota_tokens)

@app.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = get_all_users(db)  # You need to implement this in your crud.py
    return users


@app.get("/users/{user_id}/tokens")
def get_tokens_for_user(user_id: int, db: Session = Depends(get_db)):
    tokens = db.query(Token).filter(Token.user_id == user_id).all()
    return tokens
