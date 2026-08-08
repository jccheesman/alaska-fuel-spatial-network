from pathlib import Path

import duckdb

# repo root is two levels above workflows/04_duckdb_export/
DB_PATH = Path(__file__).resolve().parents[2] / "outputs" / "fuel_network.duckdb"
con = duckdb.connect(str(DB_PATH), read_only=True)

try:
    print("=== Checking edge_month_weights ===")
    has_table = con.execute("SELECT 1 FROM information_schema.tables WHERE table_name='edge_month_weights'").fetchone()
    if not has_table:
        print("Table edge_month_weights does not exist.")
    else:
        print("\nWaterway passability by month:")
        print(con.execute("SELECT month, avg(case when passable then 1.0 else 0.0 end) as passable_frac, count(*) as cnt FROM edge_month_weights WHERE mode='Barge' GROUP BY month ORDER BY month").df())
        
        print("\nIceRoad passability by month:")
        print(con.execute("SELECT month, avg(case when passable then 1.0 else 0.0 end) as passable_frac, count(*) as cnt FROM edge_month_weights WHERE mode='IceRoad' GROUP BY month ORDER BY month").df())

        # NOTE: mode='Road' aggregates Road + Join + Bridge edges (all map to
        # the 'Road' rate-mode in EDGE_TYPE_MAP), so this row is overland, not
        # Road-only. 'Plane' covers Air edges.
        print("\nOverland(Road/Join/Bridge)/Plane/Transfer passability by mode:")
        print(con.execute("SELECT mode, avg(case when passable then 1.0 else 0.0 end) as passable_frac FROM edge_month_weights WHERE mode IN ('Plane', 'Transfer') OR mode='Road' GROUP BY mode").df())

except Exception as e:
    print(e)
finally:
    con.close()
