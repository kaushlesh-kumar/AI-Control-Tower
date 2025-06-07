from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    tokens = relationship("Token", back_populates="owner")

class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(255),nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    owner = relationship("User", back_populates="tokens")
    policies = relationship("TokenPolicy", back_populates="token") 

class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    endpoint = Column(String(255))
    request_time = Column(DateTime, default=datetime.utcnow)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)

# --- Token Policies (Access Control) ---
class TokenPolicy(Base):
    __tablename__ = 'token_policies'
    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    model_name = Column(String(255), nullable=False)
    rate_limit_per_minute = Column(Integer, nullable=False, default=60)
    monthly_quota_tokens = Column(Integer, nullable=True)  # Optional

    token = relationship("Token", back_populates="policies")

