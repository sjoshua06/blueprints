import faiss
import numpy as np
import os

# Must match INDEX_DIR in faiss_manager.py exactly — both resolve to
# <project_root>/faiss_indexes regardless of working directory.
INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "faiss_indexes")


def search_similar(subcategory, vector, k=5):

    safe_name  = subcategory.lower().replace(" ", "_")
    index_path = os.path.join(INDEX_DIR, f"{safe_name}.index")
    ids_path   = os.path.join(INDEX_DIR, f"{safe_name}_ids.npy")

    if not os.path.exists(index_path):
        print(f"No FAISS index found for subcategory: {subcategory}")
        return []

    index = faiss.read_index(index_path)
    ids   = np.load(ids_path)

    query = np.array([vector]).astype("float32")

    # k+1 so we can drop the self-match (distance=0)
    distances, indices = index.search(query, min(k + 1, index.ntotal))

    results = []

    for dist, idx in zip(distances[0], indices[0]):

        if idx < 0:
            continue

        cid = int(ids[idx])

        # skip exact self-match
        if dist == 0.0 and len(results) == 0:
            continue

        results.append({
            "component_id": cid,
            "distance":     float(dist),
        })

        if len(results) >= k:
            break

    return results