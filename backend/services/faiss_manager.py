import faiss
import numpy as np
import os

# Local Storage Path
INDEX_DIR = os.path.join(os.path.dirname(__file__), "indexes")
os.makedirs(INDEX_DIR, exist_ok=True)

def create_faiss_indexes(component_vectors, user_id=None):
    """
    Creates and saves FAISS indexes locally.
    Note: user_id is ignored to revert to the legacy global-index behavior if requested,
    but we keep the parameter to maintain compatibility with existing call sites.
    """
    for subcategory, items in component_vectors.items():
        if not items:
            continue
            
        vectors = np.array([i["vector"] for i in items]).astype("float32")
        ids     = np.array([i["component_id"] for i in items])

        # Create FlatL2 index
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)

        safe_name = subcategory.lower().replace(" ", "_").replace("/", "_")
        
        # Save locally
        index_path = os.path.join(INDEX_DIR, f"{safe_name}.index")
        ids_path   = os.path.join(INDEX_DIR, f"{safe_name}_ids.npy")
        
        faiss.write_index(index, index_path)
        np.save(ids_path, ids)
        
    return {"message": "Local FAISS indexes built successfully"}