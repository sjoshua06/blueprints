from services.vector_search import search_similar
from services.compatibility_service import compatibility_score
from services.vector_builder import build_vector_from_component
from services.spec_loader import load_component_specs
from services.component_lookup import get_component_details
from sqlalchemy import text
from db.database import engine


def analyze_bom(bom_df, receipts_df):

    # Load specs once for all iterations
    specs_df = load_component_specs()

    results = []

    for _, row in bom_df.iterrows():

        # ── BOM row uses component_id directly ───────────────────────────
        component_id   = int(row["component_id"])
        component_name = str(row["component_name"])
        required_qty   = int(row["quantity_required"])

        # ── Match receipts by component_id (not component_name) ──────────
        receipt_rows = receipts_df[
            receipts_df["component_id"] == component_id
        ]

        received_qty = 0
        if not receipt_rows.empty:
            received_qty = int(receipt_rows["quantity_received"].sum())

        missing_qty = required_qty - received_qty

        if missing_qty <= 0:
            continue

        # ── Fetch component_type from DB using component_id ───────────────
        # BUG 1 FIX: the original code did:
        #   WHERE component_name = :name  +  fetchone()
        # component_name is NOT unique — "Copper Component" maps to 59
        # different component_ids. fetchone() always returned the same
        # first row, so every Copper BOM entry queried the exact same
        # vector → identical FAISS results and alternatives for all of them.
        query = text("""
            SELECT component_id, component_type, subcategory
            FROM components
            WHERE component_id = :cid
        """)

        with engine.connect() as conn:
            result = conn.execute(query, {"cid": component_id}).fetchone()

        if not result:
            continue

        component_type = str(result.component_type)
        subcategory    = str(result.subcategory)

        # ── Build vector for this specific component_id ───────────────────
        # build_vector_from_component now returns (vector, subcategory)
        vector, subcat = build_vector_from_component(component_id, specs_df)

        if vector is None:
            continue

        # ── FAISS search — routed by SUBCATEGORY ─────────────────────────
        # BUG 2 FIX: previously passed component_type to search_similar.
        # The FAISS index is now keyed by subcategory (one homogeneous
        # feature space per index), so we pass subcategory instead.
        similar = search_similar(subcat, vector)

        if not similar:
            continue

        # ── Normalise compatibility scores across this result set ─────────
        # BUG 3 FIX: compatibility_score now needs max_distance so it can
        # return a properly normalised 0–100 value.
        max_dist = max(s["distance"] for s in similar)

        alternatives = []

        for s in similar:

            component_details = get_component_details(int(s["component_id"]))

            if not component_details:
                continue

            alternatives.append({
                "component_id":       int(s["component_id"]),
                "component_name":     component_details["component_name"],
                "compatibility_score": compatibility_score(
                    s["distance"], max_dist
                ),
                "suppliers": component_details["suppliers"],
            })

        results.append({
            "component_id":          component_id,
            "component":             component_name,
            "required":              required_qty,
            "received":              received_qty,
            "missing":               missing_qty,
            "compatible_components": alternatives,
        })

    return results