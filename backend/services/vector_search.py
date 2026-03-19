import faiss
import numpy as np
import os

# Local Storage Path
INDEX_DIR = os.path.join(os.path.dirname(__file__), "indexes")

def search_similar(query_vector, subcategory, user_id=None, k=5):
    """
    Searches for similar components using local FAISS indexes.
    """
    safe_name = subcategory.lower().replace(" ", "_").replace("/", "_")
    
    index_path = os.path.join(INDEX_DIR, f"{safe_name}.index")
    ids_path   = os.path.join(INDEX_DIR, f"{safe_name}_ids.npy")
    
    # Check if files exist locally
    if not (os.path.exists(index_path) and os.path.exists(ids_path)):
        return []
        
    try:
        # Load locally
        index = faiss.read_index(index_path)
        ids   = np.load(ids_path)
        
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