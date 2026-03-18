import faiss
import numpy as np
import os

# Absolute path relative to this file's location so it works regardless
# of what directory uvicorn is launched from.
# Result: <project_root>/services/../faiss_indexes  →  <project_root>/faiss_indexes
INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "faiss_indexes")


def create_faiss_indexes(component_vectors):

    # Create the directory here (inside the function) not at import time.
    # At import time the working directory may not be the project root,
    # so os.makedirs at module level creates the folder in the wrong place
    # and faiss.write_index still fails because it uses a relative path.
    os.makedirs(INDEX_DIR, exist_ok=True)

    for subcategory, items in component_vectors.items():

        vectors       = []
        component_ids = []

        for item in items:
            vectors.append(item["vector"])
            component_ids.append(item["component_id"])

        vectors = np.array(vectors).astype("float32")
        dimension = vectors.shape[1]

        index = faiss.IndexFlatL2(dimension)
        index.add(vectors)

        safe_name  = subcategory.lower().replace(" ", "_")
        index_path = os.path.join(INDEX_DIR, f"{safe_name}.index")
        ids_path   = os.path.join(INDEX_DIR, f"{safe_name}_ids.npy")

        faiss.write_index(index, index_path)
        np.save(ids_path, np.array(component_ids))

        print(f"Created index: {safe_name} ({len(vectors)} vectors, dim={dimension})")