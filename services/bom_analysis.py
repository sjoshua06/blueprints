from services.vector_search import search_similar
from services.compatibility_service import compatibility_score
from services.vector_builder import build_vector_from_component
from services.spec_loader import load_component_specs
from sqlalchemy import text
from db.database import engine
from services.component_lookup import get_component_details


def analyze_bom(bom_df, receipts_df):

    # load specs once
    specs_df = load_component_specs()

    results = []

    for _, row in bom_df.iterrows():

        component_name = str(row["component_name"])
        required_qty = int(row["quantity_required"])

        # find received quantity from receipt file
        receipt_row = receipts_df[
            receipts_df["component_name"] == component_name
        ]

        received_qty = 0

        if not receipt_row.empty:
            received_qty = int(receipt_row["quantity_received"].sum())

        missing_qty = required_qty - received_qty

        # if nothing missing skip
        if missing_qty <= 0:
            continue

        # get component info from database
        query = text("""
        SELECT component_id, component_type
        FROM components
        WHERE component_name = :name
        """)

        with engine.connect() as conn:
            result = conn.execute(query, {"name": component_name}).fetchone()

        if not result:
            continue

        component_id = int(result.component_id)
        component_type = str(result.component_type)

        # build vector for FAISS search
        vector = build_vector_from_component(component_id, specs_df)

        if vector is None:
            continue

        # FAISS similarity search
        similar = search_similar(component_type, vector)

        alternatives = []

        for s in similar:

            component_details = get_component_details(int(s["component_id"])
)

            if component_details:

                alternatives.append({
                    "component_name": component_details["component_name"],
                    "compatibility_score": float(
                        compatibility_score(s["distance"])
                    ),
                    "suppliers": component_details["suppliers"]
                })

        results.append({
            "component": component_name,
            "required": required_qty,
            "received": received_qty,
            "missing": missing_qty,
            "compatible_components": alternatives
        })

    return results