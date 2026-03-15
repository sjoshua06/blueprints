import faiss
import numpy as np
import os

INDEX_DIR = "faiss_indexes"

def search_similar(component_type, vector, k=5):

    safe_type = component_type.lower().replace(" ", "_")

    index = faiss.read_index(f"{INDEX_DIR}/{safe_type}.index")

    ids = np.load(f"{INDEX_DIR}/{safe_type}_ids.npy")

    query = np.array([vector]).astype("float32")

    distances, indices = index.search(query, k)

    results = []

    for i, idx in enumerate(indices[0]):

        results.append({
            "component_id": int(ids[idx]),
            "distance": float(distances[0][i])
        })

    return results