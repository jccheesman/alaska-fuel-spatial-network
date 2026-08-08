"""qa_river_ice_thresholds.py

One-shot diagnostic to inform RIVER_ICE_THRESHOLD selection.

Loads the 12 monthly river_ice_MM.tif rasters from friction_inputs and
reports, for each month and overall:

  * how many valid (in-river-mask) pixels exist
  * the distribution of p_ice values across operationally-meaningful bins
  * how many pixels each candidate threshold (0.05, 0.10, 0.15, 0.20,
    0.30, 0.50) would mark as "iced / not navigable"

The decision question this answers: if we move RIVER_ICE_THRESHOLD from
0.5 to 0.15 (to mirror sea_ice on the parity argument), how many more
pixels become impassable for the barge mode — and where does the
marginal mass live?

Output:
  * stdout table of per-month and overall histograms
  * friction_outputs/river_ice_threshold_histogram.png — visual

Run:
    python -m friction_surface.qa.qa_river_ice_thresholds
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import rasterio

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR = Path(__file__).parent.parent / "friction_inputs" / "river_ice"
OUTPUT_PLOT = Path(__file__).parent.parent / "friction_outputs" / "river_ice_threshold_histogram.png"

# Bin edges chosen around the threshold candidates (0.05 / 0.10 / 0.15 /
# 0.30 / 0.50). Right-open intervals — last bin is closed at 1.0.
BIN_EDGES = np.array([0.0, 0.05, 0.10, 0.15, 0.30, 0.50, 1.0001])
BIN_LABELS = [
    "[0.00, 0.05)  certainly clear",
    "[0.05, 0.10)  marginal — blocked by 0.05",
    "[0.10, 0.15)  marginal — blocked by 0.10",
    "[0.15, 0.30)  meaningful ice — blocked by 0.15",
    "[0.30, 0.50)  substantial ice — blocked by 0.30",
    "[0.50, 1.00]  mostly/fully iced — currently blocked",
]

CANDIDATE_THRESHOLDS = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]

# Months grouped for narrative reporting. Shoulder months are where the
# threshold choice matters most; deep winter and deep summer should be
# bimodal (~all iced / all clear).
SHOULDER_MONTHS = (5, 6, 10, 11)
WINTER_MONTHS = (1, 2, 3, 4, 12)
SUMMER_MONTHS = (7, 8, 9)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_month(month: int) -> np.ndarray:
    """Return a 1-D array of valid (in-mask) p_ice values for the month.

    Pixels equal to the source NoData sentinel (off-river) are dropped.
    Pixels with value 0 inside the mask are kept — they're real "no ice"
    observations from the Brown product, not missing data.
    """
    path = INPUT_DIR / f"river_ice_{month:02d}.tif"
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float32)
        nodata = src.nodata
    flat = arr.ravel()
    valid = np.isfinite(flat)
    if nodata is not None:
        valid &= flat != np.float32(nodata)
    # Defensive: river_ice should be 0-1; clamp any tiny float drift and
    # drop pixels far outside the documented range so a single corrupt
    # cell doesn't blow up the histogram.
    in_range = (flat >= -0.01) & (flat <= 1.01)
    return np.clip(flat[valid & in_range], 0.0, 1.0)


def histogram_row(vals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    counts, _ = np.histogram(vals, bins=BIN_EDGES)
    pct = 100.0 * counts / max(vals.size, 1)
    return counts, pct


def threshold_block_counts(vals: np.ndarray) -> dict[float, tuple[int, float]]:
    """How many pixels would each candidate threshold mark as blocked."""
    out: dict[float, tuple[int, float]] = {}
    for thr in CANDIDATE_THRESHOLDS:
        blocked = int((vals > thr).sum())
        pct = 100.0 * blocked / max(vals.size, 1)
        out[thr] = (blocked, pct)
    return out


def fmt_count(n: int) -> str:
    return f"{n:>10,}"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def print_per_month_table(per_month: dict[int, np.ndarray]) -> None:
    print()
    print("=" * 96)
    print("Per-month histogram of in-river p_ice values")
    print("=" * 96)
    header = f"{'M':>3}  {'n_valid':>10}  " + "  ".join(
        f"{lab.split('  ')[0]:>12}" for lab in BIN_LABELS
    )
    print(header)
    print("-" * len(header))
    for m in range(1, 13):
        vals = per_month[m]
        counts, pct = histogram_row(vals)
        cells = "  ".join(f"{p:>11.2f}%" for p in pct)
        print(f"{m:>3}  {fmt_count(vals.size)}  {cells}")
    print()


def print_threshold_table(per_month: dict[int, np.ndarray]) -> None:
    print("=" * 96)
    print("Per-month % of pixels blocked at each candidate threshold")
    print("=" * 96)
    header = f"{'M':>3}  " + "  ".join(
        f"thr>{thr:.2f}" for thr in CANDIDATE_THRESHOLDS
    )
    print(header)
    print("-" * len(header))
    for m in range(1, 13):
        vals = per_month[m]
        blk = threshold_block_counts(vals)
        cells = "  ".join(f"{blk[thr][1]:>6.2f}%" for thr in CANDIDATE_THRESHOLDS)
        print(f"{m:>3}  {cells}")
    print()


def print_group_summary(per_month: dict[int, np.ndarray]) -> None:
    print("=" * 96)
    print("Grouped summary  (concatenated pixel populations)")
    print("=" * 96)
    groups = {
        "winter   (Jan-Apr, Dec)": WINTER_MONTHS,
        "shoulder (May, Jun, Oct, Nov)": SHOULDER_MONTHS,
        "summer   (Jul, Aug, Sep)": SUMMER_MONTHS,
    }
    for label, months in groups.items():
        vals = np.concatenate([per_month[m] for m in months])
        counts, pct = histogram_row(vals)
        blk = threshold_block_counts(vals)
        print(f"\n  {label}   (n = {vals.size:,})")
        for lab, p in zip(BIN_LABELS, pct):
            print(f"      {lab:<55} {p:>6.2f}%")
        print("    candidate thresholds  (% pixels blocked):")
        for thr in CANDIDATE_THRESHOLDS:
            print(f"      thr > {thr:.2f}   →  {blk[thr][0]:>10,}  ({blk[thr][1]:>5.2f}%)")
    print()


def print_decision_lines(per_month: dict[int, np.ndarray]) -> None:
    print("=" * 96)
    print("Decision summary  —  shoulder months only (where threshold matters)")
    print("=" * 96)
    vals = np.concatenate([per_month[m] for m in SHOULDER_MONTHS])
    blk = threshold_block_counts(vals)
    n = vals.size
    print(f"  n shoulder-month river pixels = {n:,}\n")
    print("  Currently  RIVER_ICE_THRESHOLD = 0.50")
    print(f"     blocks  {blk[0.50][0]:>10,}  ({blk[0.50][1]:>5.2f}%) of shoulder-pixel-months")
    for thr in (0.30, 0.20, 0.15, 0.10, 0.05):
        delta_n = blk[thr][0] - blk[0.50][0]
        delta_pct = blk[thr][1] - blk[0.50][1]
        print(
            f"  Would 0.{int(thr * 100):02d} block:  {blk[thr][0]:>10,}  "
            f"({blk[thr][1]:>5.2f}%)   "
            f"delta vs 0.50 = +{delta_n:>9,}  (+{delta_pct:>5.2f} pp)"
        )
    print()


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
def plot_histograms(per_month: dict[int, np.ndarray], out: Path) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 4, figsize=(15, 9), sharex=True, sharey=True)
    for m, ax in zip(range(1, 13), axes.ravel()):
        vals = per_month[m]
        # Drop the dominant 0-spike so the marginal regime is visible —
        # rivers are essentially binary (clear vs iced), and a linear
        # axis would otherwise show one tall bar at 0 and nothing else.
        positive = vals[vals > 0.0]
        ax.hist(positive, bins=50, range=(0.0, 1.0),
                color="#1f4e79", edgecolor="white", linewidth=0.3)
        ax.axvline(0.15, color="#d73027", linestyle="--", linewidth=1.2,
                   label="0.15 (sea-ice parity)")
        ax.axvline(0.50, color="#7a3b9c", linestyle=":", linewidth=1.2,
                   label="0.50 (current)")
        ax.set_title(f"Month {m:02d}  (n>0: {positive.size:,} / {vals.size:,})",
                     fontsize=9)
        ax.set_yscale("log")
        ax.tick_params(labelsize=8)
        if m == 1:
            ax.legend(fontsize=7, loc="upper right")
    fig.suptitle(
        "River-ice p_ice distribution by month  "
        "(in-river pixels with p_ice > 0; log y)",
        fontsize=12,
    )
    fig.text(0.5, 0.04, "p_ice  (climatological monthly ice-cover fraction)",
             ha="center", fontsize=10)
    fig.text(0.04, 0.5, "pixel count (log scale)", va="center",
             rotation="vertical", fontsize=10)
    fig.tight_layout(rect=(0.05, 0.05, 1, 0.96))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    per_month: dict[int, np.ndarray] = {}
    for m in range(1, 13):
        per_month[m] = load_month(m)
        logger.info("  month %02d  n_valid=%s  mean=%.4f  median=%.4f",
                    m, f"{per_month[m].size:,}",
                    float(per_month[m].mean()) if per_month[m].size else float("nan"),
                    float(np.median(per_month[m])) if per_month[m].size else float("nan"))

    print_per_month_table(per_month)
    print_threshold_table(per_month)
    print_group_summary(per_month)
    print_decision_lines(per_month)
    plot_histograms(per_month, OUTPUT_PLOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
