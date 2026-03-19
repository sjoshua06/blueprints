import pandas as pd
from db.database import engine

from sqlalchemy import text

def load_component_specs(user_id: str):

    query = text("""
    SELECT
        c.component_id,
        c.component_type,
        c.subcategory,
        cs.spec_name,
        cs.spec_value
    FROM components c
    JOIN component_specifications cs
    ON c.component_id = cs.component_id
    WHERE c.user_id = :uid
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"uid": user_id})

    return df