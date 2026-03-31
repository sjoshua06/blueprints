from sentence_transformers import SentenceTransformer

# Load the local NLP model globally (caches to disk, ~80MB)
# Generates rich 384-dimensional mathematical arrays representing the semantic meaning of electronics
model = SentenceTransformer('all-MiniLM-L6-v2')

def build_vectors(df):
    """
    Groups specifications by component and generates a dense text embedding
    using unstructured natural language models rather than rigid numeric schemas.
    """
    component_vectors = {}
    grouped = df.groupby("component_id")

    for component_id, group in grouped:
        subcategory    = group["subcategory"].iloc[0]
        component_type = group["component_type"].iloc[0]
        
        # component_name might not be in specs_df if the df doesn't JOIN components. 
        # In setup_pipeline, load_component_specs returns rows with spec_name/spec_value.
        # Let's handle it gracefully if component_name exists.
        component_name = str(group["component_name"].iloc[0]) if "component_name" in group.columns else f"Component {component_id}"

        description_parts = [
            f"Component Name: {component_name}",
            f"Type: {component_type}",
            f"Subcategory: {subcategory}",
            "Specifications:"
        ]

        # Extract all specifications as flat text
        for _, row in group.iterrows():
            spec = row["spec_name"]
            val  = row["spec_value"]
            description_parts.append(f"- {spec}: {val}")

        full_text = "\n".join(description_parts)

        # Generate the dense embedding vector
        embedding = model.encode(full_text)
        vector = embedding.tolist()

        component_vectors.setdefault(subcategory, [])
        component_vectors[subcategory].append({
            "component_id": component_id,
            "component_type": component_type,
            "vector": vector,
        })

    return component_vectors


def build_vector_from_component(component_id, df):
    """
    Used when looking up an exact component ID from the specs dataframe.
    """
    group = df[df["component_id"] == component_id]

    if group.empty:
        return None, None

    subcategory    = group["subcategory"].iloc[0]
    component_type = group["component_type"].iloc[0]
    component_name = str(group["component_name"].iloc[0]) if "component_name" in group.columns else f"Component {component_id}"

    description_parts = [
        f"Component Name: {component_name}",
        f"Type: {component_type}",
        f"Subcategory: {subcategory}",
        "Specifications:"
    ]

    for _, row in group.iterrows():
        spec = row["spec_name"]
        val  = row["spec_value"]
        description_parts.append(f"- {spec}: {val}")

    full_text = "\n".join(description_parts)
    
    embedding = model.encode(full_text)
    vector = embedding.tolist()

    return vector, subcategory

def build_vector_from_text(raw_text):
    """
    Returns a dense semantic vector directly from pure unstructured text!
    This completely solves the "missing component" lookup problem.
    """
    embedding = model.encode(raw_text)
    return embedding.tolist()