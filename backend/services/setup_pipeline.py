from services.spec_loader import load_component_specs
from services.vector_builder import build_vectors
from services.faiss_manager import create_faiss_indexes


def run_setup_pipeline(user_id: str):

    df = load_component_specs(user_id)

    vectors = build_vectors(df)

    create_faiss_indexes(vectors, user_id)

    return {"status": "indexes_created"}