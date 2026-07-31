"""friction_surface package.

Deterministic, agent-free friction-surface construction for the DOE_MAS
Alaska bulk-fuel logistics graph. This package is the repo's config +
surface-builder *core*: root-level modules (build_corridor_masks,
weight_network_edges, pipeline) import from it. It is not a
standalone distributable — see README_friction.md for the module map and the
library-vs-scripts split.

The names re-exported below are the intended public surface. Importing the
package is cheap (numpy + rasterio via the surface builder); matplotlib and
scipy stay lazy inside the functions that need them, so ``import
friction_surface`` does not pull the plotting/scientific stack.
"""

from __future__ import annotations

# Surface builder (pure numpy / rasterio) --------------------------------
from .friction_surface import build_mode_friction, write_friction_stack

# Constants — single source of truth in friction_config ------------------
from .friction_config import (
    CRS_TARGET,
    TARGET_RESOLUTION,
    FRICTION_NODATA,
    MODES,
    ICE_ROAD_SEASON_MONTHS,
    MARINE_LINEHAUL_SEASON_MONTHS,
    DELIVERY_METHOD_TO_MODES,
    MODE_TO_NETWORK,
)

# Cost rates and intermodal fees — separate from friction (never fold cost
# into the environmental surface); see friction_costs for the rationale.
from .friction_costs import (
    BASELINE_RATES_PER_GALLON_MILE,
    INTERMODAL_TRANSFER_FEES,
    MODE_METADATA,
    DEFAULT_REPR_MONTHS,
    get_hub_facilities,
    chain_cost_with_transfer_fees,
    load_ice_road_communities,
)

# Path resolution (env-overridable; anchored to the repo root) -----------
from .friction_paths import (
    get_raster_dir,
    get_raster_path,
    get_network_path,
    get_friction_output_dir,
)

__all__ = [
    # surface builder
    "build_mode_friction",
    "write_friction_stack",
    # config constants
    "CRS_TARGET",
    "TARGET_RESOLUTION",
    "FRICTION_NODATA",
    "MODES",
    "ICE_ROAD_SEASON_MONTHS",
    "MARINE_LINEHAUL_SEASON_MONTHS",
    "DELIVERY_METHOD_TO_MODES",
    "MODE_TO_NETWORK",
    # costs
    "BASELINE_RATES_PER_GALLON_MILE",
    "INTERMODAL_TRANSFER_FEES",
    "MODE_METADATA",
    "DEFAULT_REPR_MONTHS",
    "get_hub_facilities",
    "chain_cost_with_transfer_fees",
    "load_ice_road_communities",
    # paths
    "get_raster_dir",
    "get_raster_path",
    "get_network_path",
    "get_friction_output_dir",
]
