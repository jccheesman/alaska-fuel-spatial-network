"""Inspection + step-report helpers — the presentation/evaluation layer.

Pure: these never call a build step. They turn a step's input/output into something you can
*evaluate* — `describe_output` (schema, counts, distributions), `diff_columns` (what changed),
`row_delta` (row movement), and `write_step_report` (a durable `reports/NN_<step>.md` whose
feedback block is preserved across re-runs). Reports land under the project root
(:func:`mmnet.config.project_root`).
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

# Columns worth a value_counts() when present — the categorical levers each step sets.
_CATEGORICAL_HINTS = (
    "mode", "delivery_method", "hub_type", "snap_source", "assigned_level",
    "type", "edge_label", "town", "community", "hub_community", "is_hub", "is_giant",
)

# Feedback block markers: text between them is preserved when a report is re-written.
_FB_START = "<!-- FEEDBACK:START (your notes below are preserved on re-run) -->"
_FB_END = "<!-- FEEDBACK:END -->"


def _project() -> Path:
    from .config import project_root

    return project_root()


def _has_geom(df) -> bool:
    return isinstance(df, gpd.GeoDataFrame) and "geometry" in df.columns and df.geometry.notna().any()


def _schema(df) -> dict:
    """col -> dtype string, geometry last."""
    cols = [c for c in df.columns if c != "geometry"]
    out = {c: str(df[c].dtype) for c in cols}
    if "geometry" in df.columns:
        out["geometry"] = "geometry"
    return out


def summarize_gdf(gdf, name: str = "", n: int = 5) -> dict:
    """Quick look: row count, CRS, geom type, columns, and `.head(n)`.

    Prints a compact block and returns a dict you can assert on.
    """
    crs = getattr(gdf, "crs", None)
    geom_types = sorted(gdf.geom_type.unique().tolist()) if _has_geom(gdf) else []
    info = {
        "name": name,
        "n_rows": int(len(gdf)),
        "crs": str(crs) if crs is not None else None,
        "geom_types": geom_types,
        "columns": [c for c in gdf.columns],
    }
    print(f"[{name}] rows={info['n_rows']}  crs={info['crs']}  geom={geom_types or '-'}")
    print(f"  columns: {info['columns']}")
    with pd.option_context("display.max_columns", None, "display.width", 160):
        head = gdf.drop(columns="geometry") if "geometry" in gdf.columns else gdf
        print(head.head(n).to_string())
    return info


def describe_output(gdf, name: str = "") -> dict:
    """The full 'what is the output of this step' spec.

    Returns a dict with: row count, CRS, geometry types, the column->dtype schema,
    value_counts for known categorical columns, and (min,max) for numeric columns.
    Also prints it for inline reading.
    """
    spec = {
        "name": name,
        "n_rows": int(len(gdf)),
        "crs": str(getattr(gdf, "crs", None)),
        "geom_types": sorted(gdf.geom_type.unique().tolist()) if _has_geom(gdf) else [],
        "schema": _schema(gdf),
        "categoricals": {},
        "numeric_ranges": {},
    }
    for col in gdf.columns:
        if col == "geometry":
            continue
        s = gdf[col]
        if col in _CATEGORICAL_HINTS or str(s.dtype) in ("object", "bool", "category"):
            vc = s.value_counts(dropna=False)
            if len(vc) <= 25:
                spec["categoricals"][col] = {str(k): int(v) for k, v in vc.items()}
        if pd.api.types.is_numeric_dtype(s) and str(s.dtype) != "bool":
            if s.notna().any():
                spec["numeric_ranges"][col] = [float(s.min()), float(s.max())]

    print(f"=== OUTPUT: {name} ===")
    print(f"rows={spec['n_rows']}  crs={spec['crs']}  geom={spec['geom_types'] or '-'}")
    print("schema:")
    for c, t in spec["schema"].items():
        print(f"  {c:<22} {t}")
    if spec["categoricals"]:
        print("distributions:")
        for c, vc in spec["categoricals"].items():
            print(f"  {c}: {vc}")
    if spec["numeric_ranges"]:
        print("numeric ranges (min..max):")
        for c, (lo, hi) in spec["numeric_ranges"].items():
            print(f"  {c}: {lo:g} .. {hi:g}")
    return spec


def diff_columns(before, after) -> dict:
    """What the step changed between two frames: added / removed / dtype_changed."""
    b, a = set(before.columns), set(after.columns)
    added = sorted(a - b)
    removed = sorted(b - a)
    changed = []
    for c in sorted(a & b):
        if c == "geometry":
            continue
        if str(before[c].dtype) != str(after[c].dtype):
            changed.append(f"{c}: {before[c].dtype} -> {after[c].dtype}")
    out = {"added": added, "removed": removed, "dtype_changed": changed}
    print(f"columns added: {added or '(none)'}")
    if removed:
        print(f"columns removed: {removed}")
    if changed:
        print(f"dtype changed: {changed}")
    return out


def row_delta(before, after) -> tuple[int, int, int]:
    """(n_before, n_after, delta). Prints it."""
    nb, na = int(len(before)), int(len(after))
    print(f"rows: {nb} -> {na}  (delta {na - nb:+d})")
    return nb, na, na - nb


def _read_preserved_feedback(report_path: Path) -> str | None:
    """Return the user's feedback block from an existing report, if present."""
    if not report_path.exists():
        return None
    text = report_path.read_text()
    if _FB_START in text and _FB_END in text:
        return text.split(_FB_START, 1)[1].split(_FB_END, 1)[0].strip("\n")
    return None


def _feedback_template() -> str:
    return (
        "**Observations:** _what does the output show? (counts, distributions, geometry, anything off)_\n\n"
        "**Decision:** _keep as-is / change a parameter / change the method / change the data_\n\n"
        "**Improvement for the agent:** _the concrete change the methodology should adopt "
        "(which step, which param/function, what to do differently)_\n"
    )


def write_step_report(step_no, step_name: str, inputs, output_spec: dict,
                      col_diff: dict, delta: tuple, png_path: Path | None) -> Path:
    """Write `<project>/reports/NN_<step>.md`.

    Auto sections (inputs, output spec, columns added, row delta, map) are regenerated every
    run. The feedback block at the bottom is PRESERVED across re-runs, so your evaluation
    survives re-executing the notebook.
    """
    reports = _project() / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    nn = f"{int(step_no):02d}" if str(step_no).isdigit() else str(step_no)
    path = reports / f"{nn}_{step_name}.md"
    preserved = _read_preserved_feedback(path)

    lines = [f"# Step {nn} - {step_name}", ""]
    lines += ["## Inputs", ""]
    for i in (inputs or []):
        lines.append(f"- `{i}`")
    lines.append("")

    lines += ["## Output", ""]
    lines.append(f"- rows: **{output_spec.get('n_rows')}**")
    lines.append(f"- CRS: `{output_spec.get('crs')}`")
    gt = output_spec.get("geom_types") or []
    lines.append(f"- geometry: {', '.join(gt) if gt else '(none)'}")
    lines.append("")
    lines += ["### Schema", "", "| column | dtype |", "| --- | --- |"]
    for c, t in output_spec.get("schema", {}).items():
        lines.append(f"| `{c}` | {t} |")
    lines.append("")
    cats = output_spec.get("categoricals") or {}
    if cats:
        lines += ["### Distributions", ""]
        for c, vc in cats.items():
            lines.append(f"- `{c}`: {vc}")
        lines.append("")
    nums = output_spec.get("numeric_ranges") or {}
    if nums:
        lines += ["### Numeric ranges (min..max)", ""]
        for c, (lo, hi) in nums.items():
            lines.append(f"- `{c}`: {lo:g} .. {hi:g}")
        lines.append("")

    added = col_diff.get("added") if col_diff else None
    if added is not None:
        lines += ["## Transformation", ""]
        lines.append(f"- columns added: {added or '(none)'}")
        if col_diff.get("removed"):
            lines.append(f"- columns removed: {col_diff['removed']}")
        if col_diff.get("dtype_changed"):
            lines.append(f"- dtype changed: {col_diff['dtype_changed']}")
    if delta is not None:
        lines.append(f"- rows: {delta[0]} -> {delta[1]} (delta {delta[2]:+d})")
    lines.append("")

    if png_path is not None:
        rel = Path(png_path).relative_to(reports)
        lines += ["## Map", "", f"![{step_name}]({rel})", ""]

    lines += ["## Feedback", "", _FB_START, "", preserved or _feedback_template(), _FB_END, ""]

    path.write_text("\n".join(lines))
    print(f"report -> {path.relative_to(_project())}")
    return path


# --------------------------------------------------------------------------- connectivity / reachability
# The multimodal network's "is it connected, and what does each mode reach" layer. Pure (networkx); reads
# the `is_giant` / `component` / `is_hub` columns that `assemble.connect_multimodal` writes onto the nodes.
_CONNECTORS = {"Transfer", "Bridge"}      # edge types that are links between modes, not modes themselves


def _node_ids(nodes) -> "pd.Series":
    return nodes["node_id"] if "node_id" in nodes.columns else pd.Series(range(len(nodes)))


def _giant_set(nodes, edges, giant_col: str = "is_giant"):
    """The giant component's node-id set — from the `is_giant` column if present, else computed."""
    nid = _node_ids(nodes)
    if giant_col in nodes.columns and nodes[giant_col].notna().any():
        return set(nid[nodes[giant_col].fillna(False).astype(bool)].astype(int))
    import networkx as nx

    g = nx.Graph(); g.add_nodes_from(nid.astype(int))
    g.add_edges_from(zip(edges["from"].astype(int), edges["to"].astype(int)))
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    return set(comps[0]) if comps else set()


def connectivity_report(nodes, edges, mode_types: list | None = None,
                        hub_col: str = "is_hub", component_col: str = "component") -> dict:
    """Connectivity + per-mode + fuel-hub reachability of a built multimodal network.

    Returns `{n_nodes, n_edges, n_components, giant_frac, giant_nodes, per_mode, hubs_total,
    hubs_reachable, hubs_pct}` where `per_mode[type] = {nodes, in_giant, pct}` for each transport mode
    (edge `type`s other than Transfer/Bridge). Prints a compact block. Generalises the
    multimodal-network research prototype.
    """
    import networkx as nx

    nid = _node_ids(nodes)
    giant = _giant_set(nodes, edges)
    if component_col in nodes.columns and nodes[component_col].notna().any():
        n_comp = int(nodes[component_col].nunique())
    else:
        g = nx.Graph(); g.add_nodes_from(nid.astype(int))
        g.add_edges_from(zip(edges["from"].astype(int), edges["to"].astype(int)))
        n_comp = nx.number_connected_components(g)

    et = edges["type"]
    modes = mode_types or [t for t in et.dropna().unique() if t not in _CONNECTORS]
    per_mode = {}
    for m in modes:
        s = edges[et == m]
        ids = set(s["from"].astype(int)).union(s["to"].astype(int))
        if not ids:
            continue
        ing = sum(i in giant for i in ids)
        per_mode[m] = {"nodes": len(ids), "in_giant": ing, "pct": round(100 * ing / len(ids), 1)}

    hub_mask = nodes[hub_col].fillna(False).astype(bool) if hub_col in nodes.columns else pd.Series([], dtype=bool)
    hub_ids = set(nid[hub_mask].astype(int)) if len(hub_mask) else set()
    hubs_reach = sum(i in giant for i in hub_ids)
    N = max(len(nodes), 1)
    report = {
        "n_nodes": len(nodes), "n_edges": len(edges), "n_components": n_comp,
        "giant_frac": round(len(giant) / N, 3), "giant_nodes": len(giant),
        "per_mode": per_mode,
        "hubs_total": len(hub_ids), "hubs_reachable": hubs_reach,
        "hubs_pct": round(100 * hubs_reach / max(len(hub_ids), 1), 1),
    }
    print(f"=== CONNECTIVITY: {report['n_nodes']:,} nodes / {report['n_edges']:,} edges ===")
    print(f"components={report['n_components']}  giant={report['giant_frac']:.1%} "
          f"({report['giant_nodes']:,} nodes)")
    for m, v in per_mode.items():
        print(f"  {m:<10} {v['in_giant']:>6}/{v['nodes']:<6} in giant ({v['pct']}%)")
    print(f"  fuel hubs {hubs_reach}/{len(hub_ids)} reachable ({report['hubs_pct']}%)")
    return report


def mode_contribution(nodes, edges, mode: str, hub_col: str = "is_hub") -> dict:
    """Marginal contribution of one transport `mode`: the giant WITH vs WITHOUT it.

    "Without" drops that mode's edges AND the transfers that touch its nodes (e.g. air + airport
    transfers), then recomputes the giant. Returns `{mode, with, without, only_via_nodes, only_via_hubs}`
    where `with`/`without` = `{components, giant, hubs}` and `only_via_*` count the nodes/hubs that reach
    the giant ONLY because of this mode. Generalises the air-role research prototype.
    """
    import networkx as nx

    nid = _node_ids(nodes).astype(int)
    et = edges["type"]
    fr, to = edges["from"].astype(int), edges["to"].astype(int)
    mode_nodes = set(fr[et == mode]).union(to[et == mode])

    def _giant(mask):
        g = nx.Graph(); g.add_nodes_from(nid)
        s = edges[mask]
        g.add_edges_from(zip(s["from"].astype(int), s["to"].astype(int)))
        comps = sorted(nx.connected_components(g), key=len, reverse=True)
        return (set(comps[0]) if comps else set()), len(comps)

    drop = (et == mode) | ((et == "Transfer") & (fr.isin(mode_nodes) | to.isin(mode_nodes)))
    g_with, nc_with = _giant(pd.Series(True, index=edges.index))
    g_without, nc_without = _giant(~drop)
    only = g_with - g_without
    hub_ids = set(nid[nodes[hub_col].fillna(False).astype(bool)]) if hub_col in nodes.columns else set()
    out = {
        "mode": mode,
        "with": {"components": nc_with, "giant": len(g_with), "hubs": sum(h in g_with for h in hub_ids)},
        "without": {"components": nc_without, "giant": len(g_without), "hubs": sum(h in g_without for h in hub_ids)},
        "only_via_nodes": len(only), "only_via_hubs": len(only & hub_ids),
    }
    w, wo = out["with"], out["without"]
    print(f"=== {mode} CONTRIBUTION (with vs without) ===")
    print(f"  components {wo['components']} -> {w['components']}   giant {wo['giant']:,} -> {w['giant']:,}"
          f"   hubs {wo['hubs']} -> {w['hubs']}")
    print(f"  reachable ONLY via {mode}: {out['only_via_nodes']:,} nodes ({out['only_via_hubs']} fuel hubs)")
    return out


def write_network_report(report: dict, mode_contrib: dict | None = None, png_path: Path | None = None,
                         out_name: str = "03_network.md",
                         title: str = "Stage 03 — multimodal network: connectivity report") -> Path:
    """Write `<project>/reports/<out_name>` from `connectivity_report` (+ optional `mode_contribution`).

    `out_name`/`title` default to the Stage-03 report; Stage 04 passes its own so it writes a separate
    file and does not clobber the 03 report. Auto sections regenerate every run; the feedback block at
    the bottom is preserved (like `write_step_report`).
    """
    reports = _project() / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    path = reports / out_name
    preserved = _read_preserved_feedback(path)

    lines = [f"# {title}", ""]
    lines.append(f"- nodes / edges: **{report['n_nodes']:,}** / **{report['n_edges']:,}**")
    lines.append(f"- components: **{report['n_components']}**  ·  giant: **{report['giant_frac']:.1%}** "
                 f"({report['giant_nodes']:,} nodes)")
    lines.append(f"- fuel hubs reachable: **{report['hubs_reachable']}/{report['hubs_total']}** "
                 f"({report['hubs_pct']}%)")
    lines += ["", "### Per-mode reachability (share of each mode's nodes in the giant)", "",
              "| mode | nodes | in giant | % |", "| --- | --- | --- | --- |"]
    for m, v in report["per_mode"].items():
        lines.append(f"| {m} | {v['nodes']:,} | {v['in_giant']:,} | {v['pct']}% |")
    if mode_contrib:
        c = mode_contrib
        lines += ["", f"### Marginal contribution of the {c['mode']} mode (with vs without)", "",
                  "| metric | without | with |", "| --- | --- | --- |",
                  f"| components | {c['without']['components']} | {c['with']['components']} |",
                  f"| giant nodes | {c['without']['giant']:,} | {c['with']['giant']:,} |",
                  f"| fuel hubs in giant | {c['without']['hubs']} | {c['with']['hubs']} |",
                  "",
                  f"- **{c['only_via_nodes']:,} nodes ({c['only_via_hubs']} fuel hubs)** reach the giant "
                  f"ONLY via {c['mode']}."]
    if png_path is not None:
        lines += ["", "## Map", "", f"![network]({Path(png_path).name})"]
    lines += ["", "## Feedback", "", _FB_START, "", preserved or _feedback_template(), _FB_END, ""]
    path.write_text("\n".join(lines))
    print(f"report -> {path.relative_to(_project())}")
    return path
