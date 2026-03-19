from services.vector_search import search_similar
from services.compatibility_service import compatibility_score
from services.vector_builder import build_vector_from_component
from services.spec_loader import load_component_specs
from services.component_lookup import get_component_details
from sqlalchemy import text
from db.database import engine


def analyze_bom(bom_df, receipts_df, user_id=None):

    # Load specs once for all iterations
    specs_df = load_component_specs(user_id)

    results = []

    with engine.connect() as conn:
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

            query = text("""
                SELECT component_id, component_type, subcategory
                FROM components
                WHERE component_id = :cid
            """)

            result = conn.execute(query, {"cid": component_id}).fetchone()

            if not result:
                continue

            # component_type = str(result.component_type)
            subcategory    = str(result.subcategory)

            # ── Build vector for this specific component_id ───────────────────
            vector, subcat = build_vector_from_component(component_id, specs_df)

            if vector is None:
                continue

            # Fix: search_similar(query_vector, subcategory, ...)
            similar = search_similar(vector, subcat, user_id=user_id)

            if not similar:
                continue

            # Handle distance vs score
            dist_key = "score" if "score" in similar[0] else "distance"
            max_dist = max(s[dist_key] for s in similar)

            alternatives = []

            for s in similar:
                # Pass the active connection to prevent 100x slower connection recreating
                component_details = get_component_details(int(s["component_id"]), active_conn=conn)

                if not component_details:
                    continue

                alternatives.append({
                    "component_id":       int(s["component_id"]),
                    "component_name":     component_details["component_name"],
                    "compatibility_score": compatibility_score(
                        s[dist_key], max_dist
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