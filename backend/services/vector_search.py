import faiss
import numpy as np
import io
import tempfile
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY"))
BUCKET = "faiss-indexes"

def search_similar(subcategory, vector, user_id: str, k=5):
    safe = subcategory.lower().replace(" ", "_")

    # ── download index bytes from Supabase Storage ──
    try:
        index_bytes = supabase.storage.from_(BUCKET).download(f"{user_id}/{safe}.index")
        ids_bytes   = supabase.storage.from_(BUCKET).download(f"{user_id}/{safe}_ids.npy")
    except Exception as e:
        print(f"No FAISS index found for subcategory: {subcategory} (user: {user_id})")
        return []

    # ── load index from bytes via temp file ──
    with tempfile.NamedTemporaryFile(suffix=".index", delete=False) as tmp:
        tmp.write(index_bytes)
        tmp_path = tmp.name

    index = faiss.read_index(tmp_path)
    os.unlink(tmp_path)

    ids = np.load(io.BytesIO(ids_bytes))

    query = np.array([vector]).astype("float32")
    distances, indices = index.search(query, min(k + 1, index.ntotal))

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        cid = int(ids[idx])
        if dist == 0.0 and len(results) == 0:
            continue
        results.append({"component_id": cid, "distance": float(dist)})
        if len(results) >= k:
            break

    return results