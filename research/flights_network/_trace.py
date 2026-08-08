"""Tiny tracer for the `research/flights_network/` study (copy of the sandbox tracer).

Project ROOT is two parents up; transcript + figures land in this folder's `out/` (gitignored via
`research/**/out/`). Wires mmnet (NETWEAVE_PROFILE/PROJECT) so the study can reuse the package loaders.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NETWEAVE_PROFILE", str(ROOT / "profile.yaml"))
os.environ.setdefault("NETWEAVE_PROJECT", str(ROOT))
os.environ.setdefault("MPLBACKEND", "Agg")

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"


class Tracer:
    def __init__(self, slug: str, title: str):
        OUT.mkdir(parents=True, exist_ok=True)
        self.path = OUT / f"{slug}.md"
        self._buf: list[str] = []
        self._emit(f"# {title}\n", echo=f"\n{'='*78}\n{title}\n{'='*78}")

    def _emit(self, md: str, echo: str | None = None):
        self._buf.append(md)
        print(echo if echo is not None else md.replace("**", "").replace("`", ""))
        self.path.write_text("\n".join(self._buf) + "\n")

    def stage(self, text: str):
        self._emit(f"\n## {text}\n", echo=f"\n----- {text} -----")

    def note(self, text: str):
        self._emit(f"> {text}\n", echo=f"  · {text}")

    def kv(self, label: str, value):
        self._emit(f"- **{label}:** `{value}`", echo=f"    {label}: {value}")

    def show(self, df, label: str, n: int = 20, cols: list[str] | None = None):
        view = df[cols] if cols else df
        head = (view.drop(columns="geometry") if "geometry" in getattr(view, "columns", []) else view).head(n)
        with pd.option_context("display.max_columns", None, "display.width", 200):
            txt = head.to_string()
        self._emit(f"\n**{label}**\n\n```\n{txt}\n```", echo=f"  {label}:\n{txt}")

    def image(self, png_path, caption: str = ""):
        rel = Path(png_path).name
        self._emit(f"\n**{caption}**\n\n![{caption}]({rel})\n",
                   echo=f"  map -> {Path(png_path).relative_to(ROOT)}  ({caption})")

    def done(self):
        self._emit("\n_End._\n", echo=f"\n(saved -> {self.path.relative_to(ROOT)})")
