import pandas as pd
from db.database import engine


def load_component_specs():

    query = """
    SELECT
        c.component_id,
        c.component_type,
        cs.spec_name,
        cs.spec_value
    FROM components c
    JOIN component_specifications cs
    ON c.component_id = cs.component_id
    """

    df = pd.read_sql(query, engine)

    return df