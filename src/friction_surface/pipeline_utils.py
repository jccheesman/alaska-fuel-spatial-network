"""Shared infrastructure helpers for the friction-surface pipeline.

Logging and raster/vector directory resolution used by
`friction_surface.run_friction_pipeline`. The directory helpers live in
`friction_surface.friction_paths` and are re-exported here for backward
compatibility with existing call sites.

(Was the repo-root `pipeline.py`; renamed in the two-repo merge.)
"""

import os
import sys
import logging
from datetime import datetime

# get_raster_dir / get_vector_dir live in friction_paths; re-exported here
# for backward compatibility with older call sites.
from friction_surface.friction_paths import (  # noqa: F401
    PROJECT_ROOT,
    get_raster_dir,
    get_vector_dir,
)


def setup_logging(log_dir=None):
    """Configure logging to both console and a timestamped log file.

    Args:
        log_dir: Directory for the log file. Defaults to <repo root>/outputs,
            anchored absolutely so callers work from any CWD.
    """
    if log_dir is None:
        log_dir = os.path.join(PROJECT_ROOT, "outputs")
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
