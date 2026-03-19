from sqlalchemy import text
from db.database import engine

with engine.connect() as conn:
    with open("tables_out.txt", "w", encoding="utf-8") as f:
        f.write("TABLES:\n")
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        for t in tables:
            f.write(f"\n--- {t[0]} ---\n")
            cols = conn.execute(text(f"SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = '{t[0]}'")).fetchall()
            for c in cols:
                f.write(str(c) + "\n")
