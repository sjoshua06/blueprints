from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class ProfileCreate(BaseModel):

    user_id: UUID
    full_name: str
    email: EmailStr
    company_name: Optional[str] = None
    role: Optional[str] = "member"


class ProfileResponse(BaseModel):

    user_id: UUID
    full_name: str
    email: EmailStr
    company_name: Optional[str]
    role: str