from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parents[2] / "outputs" / "fuel_network.duckdb"

def main():
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        print("TABLES:")
        tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
        print(tables)
        
        if "network_nodes" in tables:
            print("\nNETWORK_NODES SCHEMA:")
            print(conn.execute("DESCRIBE network_nodes").fetchall())
            print("\nHUB COUNT:")
            print(conn.execute("SELECT count(*) FROM network_nodes WHERE is_hub").fetchall())
            print("\nGIANT COMPONENT NODES:")
            print(conn.execute("SELECT is_giant, count(*) FROM network_nodes GROUP BY is_giant").fetchall())
        
        if "network_edges" in tables:
            print("\nNETWORK_EDGES SCHEMA:")
            print(conn.execute("DESCRIBE network_edges").fetchall())
            print("\nEDGE COUNTS:")
            print(conn.execute("SELECT type, count(*) FROM network_edges GROUP BY type").fetchall())

        if "hub_facility_map" in tables:
            print("\nHUB_FACILITY_MAP SCHEMA:")
            print(conn.execute("DESCRIBE hub_facility_map").fetchall())
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
