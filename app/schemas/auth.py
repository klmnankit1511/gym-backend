from pydantic import BaseModel, EmailStr
from typing import List, Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    tenant_slug: Optional[str] = "demo-gym"  # Default to demo tenant


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    roles: List[str]

    class Config:
        from_attributes = True
