from sqlalchemy import text
from db.database import engine

def check_received_components(bom_df):

    results = []

    for _, row in bom_df.iterrows():

        component_name = row["component_name"]
        required = row["quantity_required"]

        query = text("""
        SELECT
            c.component_id,
            c.component_type,
            COALESCE(SUM(sr.quantity_received),0) as received
        FROM components c
        LEFT JOIN supplier_receipts sr
        ON sr.component_id = c.component_id
        WHERE c.component_name = :name
        GROUP BY c.component_id, c.component_type
        """)

        with engine.connect() as conn:

            result = conn.execute(query, {"name": component_name}).fetchone()

        if not result:
            continue

        component_id = result.component_id
        component_type = result.component_type
        received = result.received

        missing = required - received

        if missing > 0:

            results.append({
                "component_id": component_id,
                "component_name": component_name,
                "component_type": component_type,
                "required": required,
                "received": received,
                "missing": missing
            })

    return results