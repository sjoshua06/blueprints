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

def create_faiss_indexes(component_vectors, user_id: str):
    for subcategory, items in component_vectors.items():
        vectors = np.array([i["vector"] for i in items]).astype("float32")
        ids     = np.array([i["component_id"] for i in items])

        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)

        safe = subcategory.lower().replace(" ", "_")

        # ── serialize index to bytes (temp file → read → upload) ──
        with tempfile.NamedTemporaryFile(suffix=".index", delete=False) as tmp:
            faiss.write_index(index, tmp.name)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            index_bytes = f.read()
        os.unlink(tmp_path)

        # ── serialize ids to bytes ──
        ids_buf = io.BytesIO()
        np.save(ids_buf, ids)
        ids_bytes = ids_buf.getvalue()

        # ── upload both to Supabase Storage ──
        supabase.storage.from_(BUCKET).upload(
            f"{user_id}/{safe}.index", index_bytes,
            {"content-type": "application/octet-stream", "upsert": "true"}
        )
        supabase.storage.from_(BUCKET).upload(
            f"{user_id}/{safe}_ids.npy", ids_bytes,
            {"content-type": "application/octet-stream", "upsert": "true"}
        )
        print(f"Uploaded index: {user_id}/{safe} ({len(vectors)} vectors)")