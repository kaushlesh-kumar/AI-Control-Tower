# middleware/app.py

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from datetime import datetime, timedelta
from db import SessionLocal, Base, engine
import httpx
import os

# Constants
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

print(f"Decoding Using SECRET_KEY: {SECRET_KEY}")
print(f"Decoding Using ALGORITHM: {ALGORITHM}")
# DB Config
#DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://admin:dbmlflow@db:3306/mlflow")
#engine = create_engine(DB_URL)
#SessionLocal = sessionmaker(bind=engine)
#Base = declarative_base()

# DB Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    token = Column(String(255), unique=True)  # JWT
    quota_limit = Column(Integer, default=10000)
    quota_used = Column(Integer, default=0)
    quota_reset = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime,default=datetime.utcnow)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)

class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    endpoint = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)

    user = relationship("User")

class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(String(255))
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User")

class TokenPolicy(Base):
    __tablename__ = "token_policies"
    id = Column(Integer, primary_key=True)
    token_id = Column(String(255), ForeignKey('users.token'))
    model_name = Column(String(255))
    rate_limit_per_minute = Column(Integer, default=60)
    monthly_quota_tokens = Column(Integer, default=1000)

    user = relationship("User")

Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Auth Logic ---
def verify_token(token: str, db: Session, model_name: str = None):
    try:
        print(f"Verifying token: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        print(f"Decoded token payload: {payload}")
        # if user_id is None:
        #     raise HTTPException(status_code=403, detail="Invalid token payload")
        # user = db.query(User).filter(User.id == int(user_id)).first()
        # if user is None:
        #     raise HTTPException(status_code=403, detail="User not found")
        
        # Fetch user and token policies
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=403, detail="User not found")
        
        # Fetch token_id from tokens table
        token_entry = db.query(Token).filter(Token.token == token, Token.user_id == user.id).first()
        if token_entry is None:
            raise HTTPException(status_code=403, detail="Token not found or invalid")

        token_policy = db.query(TokenPolicy).filter(TokenPolicy.token_id == token_entry.id).first()
        if token_policy is None:
            raise HTTPException(status_code=403, detail="No policy associated with this token")

        # Check if the model is allowed
        if token_policy.model_name != model_name:
            raise HTTPException(status_code=403, detail=f"Model '{model_name}' is not allowed for this token")

        # Check rate limit per minute
        now = datetime.utcnow()
        recent_logs = db.query(AccessLog).filter(
            AccessLog.user_id == user.id,
            AccessLog.timestamp >= now - timedelta(minutes=1)
        ).count()
        if recent_logs >= token_policy.rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # # Check monthly quota tokens
        # if user.quota_used + token_policy.monthly_quota_tokens > user.quota_limit:
        #     raise HTTPException(status_code=429, detail="Monthly quota exceeded")

        return user
        
    except JWTError as e:
        print(f"JWTError: {e}")
        raise HTTPException(status_code=403, detail="Token invalid or expired")

def check_and_update_quota(user: User, db: Session, tokens_used: int):
    now = datetime.utcnow()
    if user.quota_reset < now - timedelta(days=30):
        user.quota_used = 0
        user.quota_reset = now

    if user.quota_used + tokens_used > user.quota_limit:
        raise HTTPException(status_code=429, detail="Quota exceeded")

    user.quota_used += tokens_used
    db.commit()

def log_access(db, user_id, endpoint, input_tokens, output_tokens):
    log = AccessLog(user_id=user_id, endpoint=endpoint,
                    input_tokens=input_tokens, output_tokens=output_tokens)
    db.add(log)
    db.commit()

# --- Proxy Endpoint ---
@app.post("/v1/chat/completions")
async def proxy(request: Request, authorization: str = Header(...), db: Session = Depends(get_db)):
    print(f"Authorization header: {authorization}")
    token = authorization.replace("Bearer ", "")
    
    payload = await request.json()
    model_name = payload.pop("model", None)

    if not model_name:
        raise HTTPException(status_code=400, detail="Model not specified")
    
    user = verify_token(token, db, model_name=model_name)
    print(f"Authenticated user: {user.name} (ID: {user.id})")

    MLFLOW_GATEWAY_URL = f"http://mlflow_ai_gateway:5100/endpoints/{model_name}/invocations"
    stream = payload.get("stream", False)
    input_tokens = len(str(payload)) // 4  # Rough estimate
    print(MLFLOW_GATEWAY_URL)

    #check_and_update_quota(user, db, input_tokens)

    if stream:
        async def stream_response():
            output_tokens = 0
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", MLFLOW_GATEWAY_URL, json=payload) as upstream_response:
                    async for line in upstream_response.aiter_lines():
                        if line.strip():
                            #output_tokens += len(line.strip()) // 4
                            yield f"{line.strip()}\n"
                    log_access(db, user.id, model_name, input_tokens, output_tokens)
        return StreamingResponse(stream_response(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(MLFLOW_GATEWAY_URL, json=payload)
            output_tokens = len(response.text) // 4
            log_access(db, user.id, model_name, input_tokens, output_tokens)
            try:
                return response.json()
            except Exception as e:
                print(f"Error parsing JSON response: {e}")
                raise HTTPException(status_code=500, detail="Invalid JSON returned from gateway")

# --- Models Listing ---
@app.get("/v1/models")
async def list_models():
    MLFLOW_ENDPOINTS_URL = "http://mlflow_ai_gateway:5100/api/2.0/endpoints/"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(MLFLOW_ENDPOINTS_URL)
            res.raise_for_status()
            data = res.json()
        except Exception:
            return {"object": "list", "data": []}

    return {
        "object": "list",
        "data": [
            {
                "id": ep["name"],
                "object": "model",
                "created": 0,
                "owned_by": "mlflow-gateway"
            }
            for ep in data.get("endpoints", [])
        ]
    }

