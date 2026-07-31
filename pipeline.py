"""Shared infrastructure helpers for the friction-surface pipeline.

Logging and raster/vector directory resolution used by
`friction_surface/run_friction_pipeline.py`. The directory helpers live in
`friction_surface.friction_paths` and are re-exported here for backward
compatibility with existing call sites.
"""

import os
import sys
import logging
from datetime import datetime

# get_raster_dir / get_vector_dir live in friction_paths; re-exported here
# for backward compatibility with older call sites.
from friction_surface.friction_paths import get_raster_dir, get_vector_dir  # noqa: F401


def setup_logging(log_dir="outputs"):
    """Configure logging to both console and a timestamped log file."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"pipeline_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    print(f"Logging to: {log_file}")
    return log_file
