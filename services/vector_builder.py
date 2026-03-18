from schemas.feature_schemas import FEATURE_SCHEMAS


def convert_value(value):

    try:
        return float(value)

    except (ValueError, TypeError):
        # Deterministic encoding for categorical text features
        return abs(hash(str(value))) % 1000


def build_vectors(df):
    """
    BUG 2 FIX: previously this grouped by component_TYPE (Mechanical,
    Electronics…) and stored everything under that key.  That mixed
    4 completely different feature schemas into one FAISS index — a
    Copper vector (Grade, Conductivity…) sitting next to an Aluminum
    vector (Alloy Grade, Temper…) with identical dimension=5 but totally
    different feature spaces.  FAISS saw the same dimensionality and
    accepted them, producing meaningless L2 distances.

    Fix: group by SUBCATEGORY (Spring, Copper, Sensor…) so every FAISS
    index contains only vectors built from the same schema.
    component_type is still stored alongside so search_similar can
    resolve the index filename from either key.
    """

    component_vectors = {}

    grouped = df.groupby("component_id")

    for component_id, group in grouped:

        subcategory    = group["subcategory"].iloc[0]
        component_type = group["component_type"].iloc[0]

        if subcategory not in FEATURE_SCHEMAS:
            print(f"Skipping unsupported subcategory: {subcategory}")
            continue

        schema = FEATURE_SCHEMAS[subcategory]
        vector = [0.0] * len(schema)

        for _, row in group.iterrows():

            spec  = row["spec_name"]
            value = row["spec_value"]

            if spec in schema:
                vector[schema.index(spec)] = convert_value(value)

        # KEY FIX: index key is now SUBCATEGORY, not component_type
        component_vectors.setdefault(subcategory, [])
        component_vectors[subcategory].append({
            "component_id":   component_id,
            "component_type": component_type,   # kept for reference
            "vector":         vector,
        })

    return component_vectors


def build_vector_from_component(component_id, df):

    group = df[df["component_id"] == component_id]

    if group.empty:
        return None, None

    subcategory = group["subcategory"].iloc[0]

    if subcategory not in FEATURE_SCHEMAS:
        print(f"Skipping unsupported subcategory: {subcategory}")
        return None, None

    schema = FEATURE_SCHEMAS[subcategory]
    vector = [0.0] * len(schema)

    for _, row in group.iterrows():

        spec  = row["spec_name"]
        value = row["spec_value"]

        if spec in schema:
            vector[schema.index(spec)] = convert_value(value)

    # Return both vector AND subcategory so the caller can route to
    # the correct FAISS index (keyed by subcategory now)
    return vector, subcategory