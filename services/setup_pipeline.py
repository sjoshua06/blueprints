from services.spec_loader import load_component_specs
from services.vector_builder import build_vectors
from services.faiss_manager import create_faiss_indexes


def run_setup_pipeline():

    df = load_component_specs()

    vectors = build_vectors(df)

    create_faiss_indexes(vectors)

    return {"status": "indexes_created"}