from sqlalchemy import text
from db.database import engine


def get_component_details(component_id):

    query = text("""
    SELECT 
        c.component_name,
        s.supplier_name,
        sc.unit_price,
        sc.lead_time_days
    FROM components c
    JOIN supplier_components sc 
        ON sc.component_id = c.component_id
    JOIN suppliers s 
        ON s.supplier_id = sc.supplier_id
    WHERE c.component_id = :component_id
    """)

    with engine.connect() as conn:

        rows = conn.execute(
            query,
            {"component_id": component_id}
        ).fetchall()

    if not rows:
        return None

    component_name = rows[0].component_name

    suppliers = []

    for r in rows:

        suppliers.append({
            "supplier_name": str(r.supplier_name),
            "price": float(r.unit_price),
            "lead_time_days": int(r.lead_time_days)
        })

    return {
        "component_name": component_name,
        "suppliers": suppliers
    }