from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text

from db.database import engine
from schemas.user_schema import ProfileCreate, ProfileResponse
from auth.dependencies import get_current_user_id

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/profile", response_model=dict)
def create_profile(
    profile: ProfileCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a user profile — user_id comes from the JWT."""

    user_query = text("""
        INSERT INTO "users" (id, email, password_hash)
        VALUES (:id, :email, :password_hash)
        ON CONFLICT (id) DO NOTHING
    """)

    profile_query = text("""
        INSERT INTO profiles
        (user_id, full_name, email, company_name, role)
        VALUES
        (:user_id, :full_name, :email, :company_name, :role)
        ON CONFLICT (user_id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            company_name = EXCLUDED.company_name
    """)

    try:
        data = profile.model_dump()
        data["user_id"] = user_id  # override with authenticated user

        user_data = {
            "id": user_id,
            "email": data["email"],
            "password_hash": "managed_by_supabase"
        }

        with engine.begin() as conn:
            conn.execute(user_query, user_data)
            conn.execute(profile_query, data)

        return {"message": "profile created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", response_model=ProfileResponse)
def get_profile(user_id: str = Depends(get_current_user_id)):
    """Get the authenticated user's profile."""

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