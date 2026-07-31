"""run_friction_pipeline.py

Build the friction-surface stage from preprocessed inputs: one static
overland.tif (sampled for all 12 months) + 12 monthly barge surfaces, plus
road_base.tif. The returned stack still keys 24 (mode, month) entries.

Per-edge weighting of the delivered network is a separate step
(load_final_network.py -> weight_network_edges.py); this stage only produces
the friction rasters those scripts sample.

No CrewAI, no LLM calls.
"""

from __future__ import annotations
import argparse
import logging
import time
from pathlib import Path
import pipeline
from .friction_surface import write_friction_stack
logger = logging.getLogger(__name__)

REQUIRED_STATIC = ("slope.tif", "lulc.tif", "permafrost.tif")


def _validate_inputs(input_dir: Path) -> None:
    missing: list[str] = []
    for name in REQUIRED_STATIC:
        if not (input_dir / name).exists():
            missing.append(name)
    for month in range(1, 13):
        for kind in ("sea_ice", "river_ice"):
            rel = f"{kind}/{kind}_{month:02d}.tif"
            if not (input_dir / rel).exists():
                missing.append(rel)
    if missing:
        raise FileNotFoundError(
            "Missing required preprocessed inputs in "
            f"{input_dir}:\n  " + "\n  ".join(missing)
        )


def _print_summary(friction_stack, t0: float) -> None:
    print("\n" + "=" * 56)
    print("Friction pipeline summary")
    print("=" * 56)
    print(f"  Surfaces written: {len(friction_stack)}")
    print(f"  Total runtime:    {time.time() - t0:.1f}s")
    print("=" * 56)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Preprocessed raster inputs (defaults to RASTER_DIR env var).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to write friction TIFs (defaults to FRICTION_DIR env var or ./friction_surface/friction_outputs/friction_stack).",
    )
    args = parser.parse_args()

    pipeline.setup_logging("outputs")
    t0 = time.time()

    from .friction_paths import get_friction_output_dir
    input_dir = Path(args.input_dir) if args.input_dir else Path(pipeline.get_raster_dir())
    output_dir = Path(args.output_dir) if args.output_dir else Path(get_friction_output_dir())

    _validate_inputs(input_dir)
    logger.info("building friction surfaces from %s", input_dir)
    friction_stack = write_friction_stack(input_dir, output_dir)
    logger.info("wrote %d friction surfaces", len(friction_stack))

    _print_summary(friction_stack, t0)


if __name__ == "__main__":
    main()
