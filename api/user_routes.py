from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from db.database import engine
from schemas.user_schema import ProfileCreate, ProfileResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/profile", response_model=dict)
def create_profile(profile: ProfileCreate):

    query = text("""
        INSERT INTO profiles
        (user_id, full_name, email, company_name, role)
        VALUES
        (:user_id, :full_name, :email, :company_name, :role)
    """)

    try:

        with engine.begin() as conn:
            conn.execute(query, profile.model_dump())

        return {"message": "profile created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: str):

    query = text("""
        SELECT *
        FROM profiles
        WHERE user_id = :user_id
    """)

    with engine.connect() as conn:

        result = conn.execute(query, {"user_id": user_id})

        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")

    return dict(row._mapping)