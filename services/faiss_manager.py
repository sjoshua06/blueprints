import faiss
import numpy as np
import os

INDEX_DIR = "faiss_indexes"

# Ensure directory exists
os.makedirs(INDEX_DIR, exist_ok=True)


def create_faiss_indexes(component_vectors):

    for component_type, items in component_vectors.items():

        vectors = []
        component_ids = []

        for item in items:
            vectors.append(item["vector"])
            component_ids.append(item["component_id"])

        vectors = np.array(vectors).astype("float32")

        dimension = vectors.shape[1]

        index = faiss.IndexFlatL2(dimension)

        index.add(vectors)

        safe_type = component_type.lower().replace(" ", "_")

        index_path = os.path.join(INDEX_DIR, f"{safe_type}.index")
        ids_path = os.path.join(INDEX_DIR, f"{safe_type}_ids.npy")

        # Save FAISS index
        faiss.write_index(index, index_path)

        # Save mapping
        np.save(ids_path, component_ids)