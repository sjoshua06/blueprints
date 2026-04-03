from services.vector_search import search_similar
from services.compatibility_service import compatibility_score
from services.vector_builder import build_vector_from_component, build_vector_from_text
from services.spec_loader import load_component_specs
from services.component_lookup import get_component_details
from sqlalchemy import text
from db.database import engine


def analyze_bom(bom_df, receipts_df, user_id=None):
    # Load specs once for all iterations
    specs_df = load_component_specs(user_id)
    
    # 1. Pre-fetch subcategories for all components in BOM
    all_bom_cids = bom_df["component_id"].unique().tolist()
    cid_metadata = {}
    if all_bom_cids:
        query = text("SELECT component_id, subcategory FROM components WHERE component_id IN :cids AND user_id = :user_id")
        with engine.connect() as conn:
            rows = conn.execute(query, {"cids": tuple(all_bom_cids), "user_id": user_id}).fetchall()
            cid_metadata = {int(r[0]): r[1] for r in rows}

    results = []
    all_similar_hits = [] # List of (bom_comp_info, similar_list)

    # 2. First pass: Find similarities and identify all candidate IDs
    all_candidate_ids = set()
    
    for _, row in bom_df.iterrows():
        component_id   = int(row["component_id"])
        component_name = str(row["component_name"])
        required_qty   = int(row["quantity_required"])

        # Match receipts
        receipt_rows = receipts_df[receipts_df["component_id"] == component_id]
        received_qty = int(receipt_rows["quantity_received"].sum()) if not receipt_rows.empty else 0
        missing_qty = required_qty - received_qty

        if missing_qty <= 0:
            continue

        subcat = cid_metadata.get(component_id)
        if not subcat:
            continue

        # Build vector using existing specs
        vector, _ = build_vector_from_component(component_id, specs_df)
        
        # MAGIC NLP FALLBACK: If component has zero specs mapped in DB, fall back to pure text semantics!
        if vector is None:
            raw_text = f"Component Name: {component_name}\nSubcategory: {subcat}"
            vector = build_vector_from_text(raw_text)
            
        if vector is None:
            continue

        # Search (now cached)
        similar = search_similar(vector, subcat, user_id=user_id)
        if not similar:
            continue

        all_similar_hits.append({
            "component_id": component_id,
            "component": component_name,
            "required": required_qty,
            "received": received_qty,
            "missing": missing_qty,
            "similar": similar
        })
        
        for s in similar:
            all_candidate_ids.add(int(s["component_id"]))

    # 3. Bulk fetch details for all candidate components
    candidate_details = {}
    if all_candidate_ids:
        # We'll use a modified version of get_component_details logic here for bulk
        query = text("""
            SELECT 
                c.component_id,
                c.component_name,
                s.supplier_name,
                s.contact_email,
                sc.unit_price,
                sc.lead_time_days
            FROM components c
            JOIN supplier_components sc 
                ON sc.component_id = c.component_id 
                AND sc.user_id = c.user_id
            JOIN suppliers s 
                ON s.supplier_id = sc.supplier_id 
                AND s.user_id = c.user_id
            WHERE c.component_id IN :cids
              AND c.user_id = :user_id
        """)
        with engine.connect() as conn:
            rows = conn.execute(query, {"cids": tuple(all_candidate_ids), "user_id": user_id}).fetchall()
            
            for r in rows:
                cid = int(r.component_id)
                if cid not in candidate_details:
                    candidate_details[cid] = {"component_name": r.component_name, "suppliers": []}
                candidate_details[cid]["suppliers"].append({
                    "supplier_name": str(r.supplier_name),
                    "contact_email": str(r.contact_email) if r.contact_email else None,
                    "price": float(r.unit_price),
                    "lead_time_days": int(r.lead_time_days)
                })

    # 4. Final pass: Assemble results
    for hit in all_similar_hits:
        similar = hit["similar"]
        dist_key = "score" if "score" in similar[0] else "distance"
        max_dist = max(s[dist_key] for s in similar)
        
        alternatives = []
        for s in similar:
            cid = int(s["component_id"])
            details = candidate_details.get(cid)
            if not details: continue
            
            alternatives.append({
                "component_id": cid,
                "component_name": details["component_name"],
                "compatibility_score": compatibility_score(s[dist_key], max_dist),
                "suppliers": details["suppliers"]
            })
            
        results.append({
            "component_id": hit["component_id"],
            "component": hit["component"],
            "required": hit["required"],
            "received": hit["received"],
            "missing": hit["missing"],
            "compatible_components": alternatives
        })

    return results