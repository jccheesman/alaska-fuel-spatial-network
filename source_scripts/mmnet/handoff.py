"""Hub handoff tables for ``final_network/`` — what stage 02 knows about every hub.

PROPOSED 2026-10-16 from the harness repository (agentic_harness_for_alaska_fuel_network).

The frozen handoff carried only the two shapefiles, so a consumer had to RE-INFER two things
the build already knows: which inventory records a hub serves (the harness used nearest hub
by distance) and what community a hub is (a majority vote over nearby facility labels). The
phase-5 hub builder makes both explicit — one hub per corrected community key, built from
named member sites, with the stage-03 placement trail saying where each hub landed. This
module writes that knowledge beside the zips, so every consumer reads the builder's answer
instead of guessing it:

  final_network/hub_members.csv   one row per (hub, raw inventory record)
      hub_id          stage-02 hub id ("Hub_12"), as in network_joined_nodes.hub_id
      hub_key         the canonical community key the hub was grouped by (workflow 00's
                      community_key, else the canonical spelling of the inventory name)
      hub_community   the display label (first inventory spelling of the group)
      hub_kind        community | remote_site | blob (unlabelled sites outside every place)
      delivery_method the hub's unioned modes ("Barge or Road")
      hub_type        Supplier | Receiver
      ast_facility_id the member SITE (an AEA ASTFacilityID, or SYN-<cluster> for a site
                      whose records carry none)
      record_id       the raw inventory record_id (workflow 00) merged into that site; empty
                      when the build ran without the record trail
      node_id         the node the hub landed on (empty when unplaced)
      snap_status     placed | merged:<hub already on that node> | unplaced:beyond_cap

  final_network/hub_snaps.csv     the stage-03 placement trail, copied verbatim
      hub_id, node_id, snap_dist_m, snap_surface, status

Both files are small (hundreds of hubs, ~2,000 records), plain CSV, LF endings, and listed in
``final_network/MANIFEST.sha256`` like the zip members. ``02_load_final_network.py`` loads them
into the DuckDB deliverable as ``hub_members`` and ``hub_snaps`` when they are present, which
closes the "hub_facility_map — documented future work" seam in DATA_CONTRACTS §8.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

HUB_MEMBERS_COLUMNS = ["hub_id", "hub_key", "hub_community", "hub_kind", "delivery_method",
                       "hub_type", "ast_facility_id", "record_id", "node_id", "snap_status"]
HUB_SNAPS_COLUMNS = ["hub_id", "node_id", "snap_dist_m", "snap_surface", "status"]


def _hub_order(hub_id: str) -> tuple:
    """Hub_2 before Hub_10: sort by the numeric suffix when there is one."""
    s = str(hub_id)
    tail = s.rsplit("_", 1)[-1]
    return (0, int(tail), s) if tail.isdigit() else (1, 0, s)


def hub_members_table(hubs: pd.DataFrame, site_members: pd.DataFrame | None,
                      hub_snaps: pd.DataFrame | None) -> pd.DataFrame:
    """Unroll ``hubs.member_site_ids`` to one row per (hub, site, raw record).

    ``hubs`` is stage 02's table (02_hubs.gpkg; geometry ignored), ``site_members`` stage 01's
    ``01_site_members.csv`` (ast_facility_id, record_id) or None when the build ran without the
    record trail, ``hub_snaps`` stage 03's ``02_hub_snaps.csv`` or None. Every hub appears at
    least once, even one with no member ids (a row with an empty site), so a consumer can count
    hubs from this file alone.
    """
    rows = []
    for h in hubs.to_dict("records"):
        v = h.get("member_site_ids")
        v = "" if v is None or (isinstance(v, float) and v != v) else str(v)   # None / NaN -> no members
        sites = [s for s in v.split(";") if s] or [""]
        for s in sites:
            rows.append({
                "hub_id": h["hub_id"],
                "hub_key": h.get("hub_key"),
                "hub_community": h.get("hub_community"),
                "hub_kind": h.get("hub_kind"),
                "delivery_method": h.get("delivery_method"),
                "hub_type": h.get("hub_type"),
                "ast_facility_id": s,
            })
    out = pd.DataFrame(rows, columns=HUB_MEMBERS_COLUMNS[:7])

    if site_members is not None and len(site_members):
        sm = site_members[["ast_facility_id", "record_id"]].astype("string")
        out = out.merge(sm, on="ast_facility_id", how="left")
    else:
        out["record_id"] = pd.Series([pd.NA] * len(out), dtype="string")

    if hub_snaps is not None and len(hub_snaps):
        hs = hub_snaps[["hub_id", "node_id", "status"]].rename(columns={"status": "snap_status"})
        hs = hs.drop_duplicates("hub_id", keep="first")
        out = out.merge(hs, on="hub_id", how="left")
    else:
        out["node_id"] = pd.NA
        out["snap_status"] = pd.NA

    out["node_id"] = pd.array(
        [None if pd.isna(v) else int(v) for v in out["node_id"]], dtype="Int64")
    out = out[HUB_MEMBERS_COLUMNS]
    out = out.assign(_o=out["hub_id"].map(_hub_order)).sort_values(
        ["_o", "ast_facility_id", "record_id"], kind="stable", na_position="last").drop(columns="_o")
    return out.reset_index(drop=True)


def write_hub_handoff(project_output: str | Path, out_dir: str | Path) -> list[Path]:
    """Read stage 01/02/03 outputs under ``project_output`` (the mmnet ``output/`` folder) and
    write ``hub_members.csv`` + ``hub_snaps.csv`` into ``out_dir`` (``final_network/``).
    Returns the written paths; returns [] when 02_hubs.gpkg is absent (an older build)."""
    import geopandas as gpd

    project_output, out_dir = Path(project_output), Path(out_dir)
    hubs_path = project_output / "02_hubs.gpkg"
    if not hubs_path.exists():
        print(f"[handoff] {hubs_path} not found — hub_members.csv / hub_snaps.csv not written")
        return []
    hubs = pd.DataFrame(gpd.read_file(hubs_path).drop(columns="geometry"))
    sm_path = project_output / "01_site_members.csv"
    hs_path = project_output / "02_hub_snaps.csv"
    site_members = pd.read_csv(sm_path, dtype="string") if sm_path.exists() else None
    hub_snaps = pd.read_csv(hs_path) if hs_path.exists() else None

    written = []
    members = hub_members_table(hubs, site_members, hub_snaps)
    p = out_dir / "hub_members.csv"
    members.to_csv(p, index=False, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    written.append(p)
    if hub_snaps is not None:
        q = out_dir / "hub_snaps.csv"
        hub_snaps[[c for c in HUB_SNAPS_COLUMNS if c in hub_snaps.columns]].to_csv(
            q, index=False, lineterminator="\n")
        written.append(q)
    n_hubs = members["hub_id"].nunique()
    n_rec = int(members["record_id"].notna().sum())
    print(f"[handoff] hub_members.csv: {len(members):,} rows, {n_hubs} hubs, {n_rec:,} inventory "
          f"records traced; hub_snaps.csv: {0 if hub_snaps is None else len(hub_snaps)} hubs")
    return written
