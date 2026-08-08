#!/usr/bin/env python3
"""Export the FINAL joined network (Stage-04) to the frozen final_network/ handoff.

Reads outputs/02_network_build/output/04_network_joined__{nodes,edges}.gpkg and
writes, into the top-level final_network/ folder consumed by workflow 03
(01_extract_network_handoff.py -> 02_load_final_network.py):

  1. network_joined_{nodes,edges}/ shapefile directories (EPSG:3338, NAD83 /
     Alaska Albers). Shapefile/DBF field names are limited to 10 characters,
     so long attribute names get ArcGIS-safe aliases (documented in
     final_network/README.md and printed below).
  2. network_joined_{nodes,edges}.zip — the committed handoff artifacts.
  3. MANIFEST.sha256 — checksums of every zip member, so a re-export that
     changes ANY byte (and therefore potentially the edge_id = row-order
     contract) is loud, not silent.

CAUTION — edge_id contract: workflow 03 keys every DuckDB table by the
0-based shapefile row order. Re-running this export after a rebuild
produces a NEW network-of-record: the committed zips, the EXPECTED
inventory in 02_load_final_network.py, and every edge_id-keyed table must
then be regenerated together (see final_network/README.md provenance note).

Run:  python workflows/02_network_build/06_export_final_network.py
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from mmnet.network import NetworkTables

ROOT = Path(__file__).resolve().parents[2]  # repo root
PROJ = ROOT / "outputs" / "02_network_build"  # mmnet project dir
OUT = ROOT / "final_network"                # the frozen handoff folder

# long name -> ArcGIS/DBF-safe (<=10 chars). Anything not listed is already <=10 and kept as-is.
NODE_RENAME = {
    "delivery_method": "deliv_meth",
    "total_hub_capacity": "hub_cap",
    "snap_surface": "snap_surf",
}
EDGE_RENAME: dict[str, str] = {}   # from/to/type/source/join_gap_m are all <=10


def _zip_shapefile_dir(shp_dir: Path, zip_path: Path) -> list[tuple[str, str]]:
    """Zip a shapefile directory (arcname = <dirname>/<file>); return (member, sha256) pairs."""
    entries = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(shp_dir.iterdir()):
            if f.is_file():
                arc = f"{shp_dir.name}/{f.name}"
                zf.write(f, arc)
                entries.append((arc, hashlib.sha256(f.read_bytes()).hexdigest()))
    return entries


def main() -> None:
    stem = PROJ / "output" / "04_network_joined"
    if not (stem.parent / "04_network_joined__edges.gpkg").exists():
        raise SystemExit(
            "outputs/02_network_build/output/04_network_joined not found — build it first: "
            "python workflows/02_network_build/04_build_network.py "
            "(needs join_components.max_dist > 0 in profile.yaml)"
        )

    nt = NetworkTables.from_gpkg(stem)
    nodes = nt.nodes.rename(columns=NODE_RENAME)
    edges = nt.edges.rename(columns=EDGE_RENAME)

    manifest_entries: list[tuple[str, str]] = []
    for name, gdf in (("network_joined_nodes", nodes), ("network_joined_edges", edges)):
        shp_dir = OUT / name
        shp_dir.mkdir(parents=True, exist_ok=True)
        gdf.to_file(shp_dir / f"{name}.shp", driver="ESRI Shapefile")
        manifest_entries += _zip_shapefile_dir(shp_dir, OUT / f"{name}.zip")
        print(f"{name}: {len(gdf):,} features -> {name}.zip (EPSG:{gdf.crs.to_epsg()})")

    manifest = OUT / "MANIFEST.sha256"
    manifest.write_text(
        "".join(f"{digest}  {member}\n" for member, digest in manifest_entries)
    )
    print(f"wrote {manifest.relative_to(ROOT)} ({len(manifest_entries)} members)")

    ncomp = int(nodes["component"].nunique())
    giant = 100 * nodes["is_giant"].fillna(False).astype(bool).mean()
    print(f"components {ncomp} · giant {giant:.2f}% · edge types "
          f"{dict(sorted(edges['type'].value_counts().to_dict().items()))}")
    print("field renames (long -> shapefile):", NODE_RENAME)
    print("\nNOTE: committed zips + workflow 03's EXPECTED inventory describe the "
          "frozen network-of-record; only commit a re-export deliberately "
          "(see final_network/README.md).")


if __name__ == "__main__":
    main()
