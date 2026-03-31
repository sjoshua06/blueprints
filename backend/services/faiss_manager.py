import faiss
import numpy as np
import os

# Local Storage Path
INDEX_DIR = os.path.join(os.path.dirname(__file__), "indexes")
os.makedirs(INDEX_DIR, exist_ok=True)

from db.supabase_client import official_supabase
import tempfile

def create_faiss_indexes(component_vectors, user_id):
    """
    Creates FAISS indexes locally in a temp folder, then uploads them
    to Supabase Storage under the user's specific folder.
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
        
        # Save to temporary directory first
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_index_path = os.path.join(tmpdir, f"{safe_name}.index")
            temp_ids_path   = os.path.join(tmpdir, f"{safe_name}_ids.npy")
            
            faiss.write_index(index, temp_index_path)
            np.save(temp_ids_path, ids)
            
            # Paths inside Supabase Storage
            storage_index_path = f"{user_id}/{safe_name}.index"
            storage_ids_path   = f"{user_id}/{safe_name}_ids.npy"
            
            # Upload (overwrite if exists)
            with open(temp_index_path, "rb") as f:
                official_supabase.storage.from_("faiss_indexes").upload(
                    storage_index_path, 
                    f.read(),
                    file_options={"upsert": "true"}
                )
            with open(temp_ids_path, "rb") as f:
                official_supabase.storage.from_("faiss_indexes").upload(
                    storage_ids_path, 
                    f.read(),
                    file_options={"upsert": "true"}
                )
        
    return {"message": "FAISS indexes built and uploaded to Supabase successfully"}