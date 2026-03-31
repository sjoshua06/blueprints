import faiss
import numpy as np
import os
import tempfile
from db.supabase_client import official_supabase

# Local Storage Path and Cache
INDEX_DIR = os.path.join(os.path.dirname(__file__), "indexes")
_INDEX_CACHE = {}
_IDS_CACHE   = {}

def search_similar(query_vector, subcategory, user_id=None, k=5):
    """
    Searches for similar components using FAISS indexes from Supabase Storage.
    Uses in-memory caching to avoid redundant downloads.
    """
    if not user_id:
        print("Error: user_id is required for user-specific FAISS search.")
        return []

    safe_name = subcategory.lower().replace(" ", "_").replace("/", "_")
    cache_key = f"{user_id}_{safe_name}"
    
    try:
        # Load from cache if available
        if cache_key in _INDEX_CACHE:
            index = _INDEX_CACHE[cache_key]
            ids   = _IDS_CACHE[cache_key]
        else:
            print(f"📥 Downloading FAISS index for {subcategory} from Supabase Storage...")
            
            storage_index_path = f"{user_id}/{safe_name}.index"
            storage_ids_path   = f"{user_id}/{safe_name}_ids.npy"
            
            # Download files
            try:
                index_data = official_supabase.storage.from_("faiss_indexes").download(storage_index_path)
                ids_data   = official_supabase.storage.from_("faiss_indexes").download(storage_ids_path)
            except Exception as e:
                print(f"Index not found in storage for {subcategory}: {e}")
                return []
                
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_index_path = os.path.join(tmpdir, "temp.index")
                temp_ids_path   = os.path.join(tmpdir, "temp.npy")
                
                with open(temp_index_path, "wb") as f:
                    f.write(index_data)
                with open(temp_ids_path, "wb") as f:
                    f.write(ids_data)
                    
                index = faiss.read_index(temp_index_path)
                ids   = np.load(temp_ids_path)
                
            _INDEX_CACHE[cache_key] = index
            _IDS_CACHE[cache_key]   = ids
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
        import traceback; traceback.print_exc()
        print(f"Error searching on {subcategory}: {e}")
        return []