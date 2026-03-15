from schemas.feature_schemas import FEATURE_SCHEMAS
def convert_value(value):

    try:
        return float(value)

    except ValueError:

        # Encode text features
        return abs(hash(value)) % 1000

def build_vectors(df):

    component_vectors = {}

    grouped = df.groupby("component_id")

    for component_id, group in grouped:

        component_type = group["component_type"].iloc[0]

        if component_type not in FEATURE_SCHEMAS:
            print(f"Skipping unsupported type: {component_type}")
            continue

        schema = FEATURE_SCHEMAS[component_type]

        vector = [0] * len(schema)

        for _, row in group.iterrows():

            spec = row["spec_name"]
            value = row["spec_value"]

            if spec in schema:

                index = schema.index(spec)

                vector[index] = convert_value(value)

        component_vectors.setdefault(component_type, [])

        component_vectors[component_type].append(
            {
                "component_id": component_id,
                "vector": vector
            }
        )

    return component_vectors

def build_vector_from_component(component_id, df):

    group = df[df["component_id"] == component_id]

    if group.empty:
        return None

    component_type = group["component_type"].iloc[0]

    if component_type not in FEATURE_SCHEMAS:
        print(f"Skipping unsupported type: {component_type}")
        return None

    schema = FEATURE_SCHEMAS[component_type]

    vector = [0] * len(schema)

    for _, row in group.iterrows():

        spec = row["spec_name"]
        value = row["spec_value"]

        if spec in schema:

            index = schema.index(spec)

            vector[index] = convert_value(value)

    return vector