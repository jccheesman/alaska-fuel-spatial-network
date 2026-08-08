"""Upstream preprocessing that produces the inputs/friction_rasters rasters.

Data-prep scripts (GEE exports, ArcGIS river-ice pipeline, grid padding/
alignment) run as ``python -m friction_surface.friction_preprocessing.<name>``
or standalone. Several depend on ``arcpy`` (Windows/ArcGIS Pro only) and are
not part of the core surface build.
"""
