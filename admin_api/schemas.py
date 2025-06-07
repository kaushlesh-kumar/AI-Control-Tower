from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str    
    email: EmailStr
    password: str

class TokenCreate(BaseModel):
    description: Optional[str] = ""
    expires_at: Optional[datetime]

class PolicyCreate(BaseModel):
    model_name: str
    rate_limit_per_minute: int
    monthly_quota_tokens: Optional[int] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    model_config = {
        "from_attributes": True
    }

class TokenOut(BaseModel):
    token: str
    description: str
    expires_at: Optional[datetime]
    model_config = {
        "from_attributes": True
    }

class PolicyOut(BaseModel):
    token: str
    model_name: str
    rate_limit: int
    quota: int
    model_config = {
        "from_attributes": True
    }
