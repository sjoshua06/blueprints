from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import List

from db.database import engine
from schemas.project_schema import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=dict)
def create_project(project: ProjectCreate):

    query = text("""
        INSERT INTO projects
        (user_id, project_name, project_description, industry_type)
        VALUES
        (:user_id, :project_name, :project_description, :industry_type)
        RETURNING project_id
    """)

    try:

        with engine.begin() as conn:

            result = conn.execute(query, project.model_dump())

            project_id = result.scalar()

        return {
            "message": "project created",
            "project_id": project_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=List[ProjectResponse])
def get_projects(user_id: str):

    query = text("""
        SELECT *
        FROM projects
        WHERE user_id = :user_id
        ORDER BY created_at DESC
    """)

    with engine.connect() as conn:

        result = conn.execute(query, {"user_id": user_id})

        rows = result.fetchall()

    return [dict(row._mapping) for row in rows]