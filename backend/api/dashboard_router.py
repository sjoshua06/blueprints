from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text

from db.database import engine
from auth.dependencies import get_current_user_id

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(user_id: str = Depends(get_current_user_id)):
    """Return aggregate counts for the authenticated user's data."""

    queries = {
        "component_count": "SELECT COUNT(*) FROM components WHERE user_id = :uid",
        "supplier_count": "SELECT COUNT(*) FROM suppliers WHERE user_id = :uid",
        "inventory_count": "SELECT COUNT(*) FROM inventory WHERE user_id = :uid",
        "supplier_component_count": "SELECT COUNT(*) FROM supplier_components WHERE user_id = :uid",
    }

    try:
        result = {}
        with engine.connect() as conn:
            for key, sql in queries.items():
                row = conn.execute(text(sql), {"uid": user_id})
                result[key] = row.scalar()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components")
def dashboard_components(user_id: str = Depends(get_current_user_id)):
    """Return all components belonging to the authenticated user."""

    query = text("""
        SELECT component_id, component_name, component_type,
               category, subcategory, manufacturer,
               part_number, description, unit_of_measure,
               lifecycle_status, created_at
        FROM components
        WHERE user_id = :uid
        ORDER BY component_id
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(query, {"uid": user_id}).fetchall()
        return [dict(r._mapping) for r in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suppliers")
def dashboard_suppliers(user_id: str = Depends(get_current_user_id)):
    """Return all suppliers belonging to the authenticated user."""

    query = text("""
        SELECT supplier_id, supplier_name, contact_email, phone,
               country, address, reliability_score, risk_score,
               on_time_delivery_rate, defect_rate,
               avg_lead_time_days, created_at
        FROM suppliers
        WHERE user_id = :uid
        ORDER BY supplier_id
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(query, {"uid": user_id}).fetchall()
        return [dict(r._mapping) for r in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory")
def dashboard_inventory(user_id: str = Depends(get_current_user_id)):
    """Return all inventory items belonging to the authenticated user."""

    query = text("""
        SELECT inventory_id, component_id, stock_quantity,
               unit_of_measure, warehouse_location,
               reorder_level, safety_stock, last_updated
        FROM inventory
        WHERE user_id = :uid
        ORDER BY inventory_id
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(query, {"uid": user_id}).fetchall()
        return [dict(r._mapping) for r in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
