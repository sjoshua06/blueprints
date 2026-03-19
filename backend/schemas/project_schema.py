from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class ProjectCreate(BaseModel):

    user_id: UUID
    project_name: str
    project_description: Optional[str] = None
    industry_type: Optional[str] = None


class ProjectResponse(BaseModel):

    project_id: int
    user_id: UUID
    project_name: str
    project_description: Optional[str]
    industry_type: Optional[str]