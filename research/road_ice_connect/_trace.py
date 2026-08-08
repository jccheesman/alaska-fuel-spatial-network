"""Tiny tracer for the `research/road_ice_connect/` methodology study.

Copy of `explain/_trace.py`, repointed: the project ROOT is two parents up (this folder sits at
`research/road_ice_connect/`), and the Markdown/PNG transcript lands in this folder's `out/`. Mirrors
every line to the terminal AND to a Markdown transcript so the gap analysis can be followed live and
re-read later. The `out/` directory is gitignored; the scripts + METHOD.md are tracked.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Project root is two levels up (research/road_ice_connect/ -> research/ -> project).
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NETWEAVE_PROFILE", str(ROOT / "profile.yaml"))
os.environ.setdefault("NETWEAVE_PROJECT", str(ROOT))
os.environ.setdefault("MPLBACKEND", "Agg")

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"


class Tracer:
    """Dual-output narrator: `print()` to the terminal and append to a Markdown file."""

    def __init__(self, slug: str, title: str):
        OUT.mkdir(parents=True, exist_ok=True)
        self.path = OUT / f"{slug}.md"
        self._buf: list[str] = []
        self._emit(f"# {title}\n", echo=f"\n{'='*78}\n{title}\n{'='*78}")

    # --- internal ---------------------------------------------------------
    def _emit(self, md: str, echo: str | None = None):
        self._buf.append(md)
        print(echo if echo is not None else md.replace("**", "").replace("`", ""))
        self.path.write_text("\n".join(self._buf) + "\n")

    # --- narration --------------------------------------------------------
    def stage(self, text: str):
        self._emit(f"\n## {text}\n", echo=f"\n----- {text} -----")

    def step(self, n, what: str):
        self._emit(f"\n### Step {n} — {what}\n", echo=f"\n[{n}] {what}")

    def note(self, text: str):
        self._emit(f"> {text}\n", echo=f"  · {text}")

    def kv(self, label: str, value):
        self._emit(f"- **{label}:** `{value}`", echo=f"    {label}: {value}")

    def delta(self, before: int, after: int, label: str = "rows"):
        self._emit(f"- {label}: **{before} → {after}** ({after-before:+d})",
                   echo=f"    {label}: {before} -> {after} ({after-before:+d})")

    def code(self, text: str):
        self._emit(f"```\n{text}\n```", echo=f"    {text}")

    # --- data display -----------------------------------------------------
    def show(self, df, label: str, n: int = 4, cols: list[str] | None = None):
        """Print row count, CRS, geometry type, columns, and a small head() table."""
        is_geo = isinstance(df, gpd.GeoDataFrame) and "geometry" in df.columns
        crs = f"EPSG:{df.crs.to_epsg()}" if is_geo and df.crs else ("—" if not is_geo else "no CRS")
        geom = ", ".join(sorted(df.geom_type.dropna().unique())) if is_geo else "table"
        view = df[cols] if cols else df
        head = view.drop(columns="geometry") if "geometry" in view.columns else view
        head = head.head(n)
        with pd.option_context("display.max_columns", None, "display.width", 200):
            txt = head.to_string()
        self._emit(
            f"\n**{label}** — rows=`{len(df)}`  crs=`{crs}`  geom=`{geom}`\n\n"
            f"columns: {', '.join(f'`{c}`' for c in df.columns)}\n\n```\n{txt}\n```",
            echo=f"  {label}: rows={len(df)} crs={crs} geom={geom}\n"
                 f"    columns: {list(df.columns)}\n{txt}",
        )

    def image(self, png_path, caption: str = ""):
        """Embed a saved PNG (in out/) into the Markdown transcript + note it on the terminal."""
        rel = Path(png_path).name          # md lives in the same out/ dir as the image
        self._emit(f"\n**{caption}**\n\n![{caption}]({rel})\n",
                   echo=f"  map -> {Path(png_path).relative_to(ROOT)}  ({caption})")

    def done(self):
        self._emit("\n_End of stage._\n", echo=f"\n(saved -> {self.path.relative_to(ROOT)})")
