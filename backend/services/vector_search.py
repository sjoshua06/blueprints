import faiss
import numpy as np
import os

# Local Storage Path and Cache
INDEX_DIR = os.path.join(os.path.dirname(__file__), "indexes")
_INDEX_CACHE = {}
_IDS_CACHE   = {}

def search_similar(query_vector, subcategory, user_id=None, k=5):
    """
    Searches for similar components using local FAISS indexes.
    Uses in-memory caching to avoid redundant disk I/O.
    """
    safe_name = subcategory.lower().replace(" ", "_").replace("/", "_")
    
    index_path = os.path.join(INDEX_DIR, f"{safe_name}.index")
    ids_path   = os.path.join(INDEX_DIR, f"{safe_name}_ids.npy")
    
    # Check if files exist locally
    if not (os.path.exists(index_path) and os.path.exists(ids_path)):
        return []
        
    try:
        # Load from cache or disk
        if safe_name in _INDEX_CACHE:
            index = _INDEX_CACHE[safe_name]
            ids   = _IDS_CACHE[safe_name]
        else:
            index = faiss.read_index(index_path)
            ids   = np.load(ids_path)
            _INDEX_CACHE[safe_name] = index
            _IDS_CACHE[safe_name]   = ids
            print(f"💾 Loaded index for {subcategory} into memory.")
        
        # Query
        query_vector = np.array([query_vector]).astype("float32")
        distances, indices = index.search(query_vector, k)
        
        # Format results
        results = [
            {"component_id": int(ids[i]), "score": float(distances[0][j])}
            for j, i in enumerate(indices[0]) if i < len(ids)
        ]
        
        return results
        
    except Exception as e:
        print(f"Error searching locally on {subcategory}: {e}")
        return []