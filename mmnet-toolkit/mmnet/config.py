"""Typed configuration for mmnet.

The engine is region-agnostic: every region-specific value lives in ONE **RegionProfile**
YAML (`examples/<region>/profile.yaml`), never in code. The profile subsumes the older
`config/layers.yaml` (the transport-layer + transfer registry, the modularity seam) and
`config/params.yaml` (the R `default_params()` equivalent) into a single validated schema.

`load_profile(path) -> RegionProfile` parses + validates the profile; paths written against named
`roots` resolve to absolute paths here, so a registry typo or a missing file is caught at load — not
mid-pipeline. `RegionProfile.to_pipeline_config()` / `.to_params()` project the profile onto the
legacy `PipelineConfig` / `Params` models the native steps already consume, so wiring the steps to
the profile is a one-line change at each call site. `load_config` / `load_params` are kept as thin
back-compat shims that prefer a profile when one is configured.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

# Project dir = the package's containing project (one parent up: mmnet/config.py -> project).
PROJECT_DIR = Path(__file__).resolve().parents[1]
# mmnet is region-agnostic and ships no bundled region: the profile is always supplied
# explicitly (`run_pipeline(profile_path)` sets MMNET_PROFILE). There is no built-in
# default profile — `load_config`/`load_params` require one.

# Env-var names: the canonical `MMNET_*` with a fallback to the legacy `NETWEAVE_*` so callers or
# scripts that still set the old names keep working (behaviour-preserving rename).
_ENV_PROFILE = ("MMNET_PROFILE", "NETWEAVE_PROFILE")
_ENV_PROJECT = ("MMNET_PROJECT", "NETWEAVE_PROJECT")


def _env_first(names: tuple[str, ...]) -> str | None:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return None


def active_profile_path() -> Path | None:
    """The profile to load, from the MMNET_PROFILE env (or legacy NETWEAVE_PROFILE), or None."""
    env = _env_first(_ENV_PROFILE)
    return Path(env) if env else None


def project_root() -> Path:
    """Where a project's outputs (`output/`) and control plane (`state/`) live.

    Resolution order:
      1. `MMNET_PROJECT` env (or legacy `NETWEAVE_PROJECT`) — an explicit project directory.
      2. The directory of the active `MMNET_PROFILE` — outputs land next to the profile, so a
         user who runs `MMNET_PROFILE=./profile.yaml python -c "import mmnet; ..."` gets results
         in their project.
      3. `PROJECT_DIR` — the dev/test/reference default when no env is set.

    Resolved at call time so each run honours its own environment.
    """
    env_proj = _env_first(_ENV_PROJECT)
    if env_proj:
        return Path(env_proj).resolve()
    env_prof = _env_first(_ENV_PROFILE)
    if env_prof:
        return Path(env_prof).resolve().parent
    return PROJECT_DIR


class _Strict(BaseModel):
    """Reject unknown keys so registry typos fail loudly at load."""

    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- legacy models
class LayerSpec(_Strict):
    name: str
    mode: str
    edge_label: str
    kind: Literal["line", "point"] = "line"
    loader: str
    paths: list[str] = Field(default_factory=list)
    extra_paths: list[str] = Field(default_factory=list)
    snap_target: bool = False   # hubs snap onto this layer's nodes (the ground surface)


class TransferSpec(_Strict):
    from_mode: str
    to_mode: str
    anchor: str
    max_dist: float


class BridgeSpec(_Strict):
    """A proximity connection policy (mmnet.connect_extras). `from_mode == to_mode` is a within-mode
    WELD (road↔road, ice↔ice); distinct modes are a cross-mode BRIDGE (ice↔road). A connector is
    added only when the real gap ≤ `max_dist` (meters)."""

    from_mode: str
    to_mode: str
    max_dist: float


class ConnectToGiantSpec(_Strict):
    """The connect-to-giant (shore-landing) pass: join every still-disconnected piece to the giant
    where it is within `max_dist` (meters). 0 disables it."""

    max_dist: float = 0.0


class JoinComponentsSpec(_Strict):
    """Stage 04: join every non-giant component to the giant when its nearest node is within
    `max_dist` (meters) of a giant node — a synthetic connector per component, iterated until
    stable. Acts on the ALL-mode component structure. 0 disables (no Stage-04 output)."""

    max_dist: float = 0.0


class SnapSpec(_Strict):
    """Snap a mode's endpoints onto another mode's nodes at an anchor — a SHARED node, no transfer edge.
    Used for airports: each `from_mode` (Plane) leg endpoint that is an `anchor` (airport) point is moved
    onto the nearest `to_mode` (Road) node within `max_dist` (meters), so air connects to road AT a node."""

    from_mode: str
    to_mode: str
    anchor: str
    max_dist: float


class CRS(_Strict):
    target: int = 3857  # neutral projected (meters) default; the profile sets the real target CRS
    input: int = 4326


class PlaceTagging(_Strict):
    places: str
    regions: str


class DeliveryFallback(_Strict):
    """Optional community→mode layer used to fill facilities whose inventory delivery_method is blank.

    `path` is a point layer; `community_col`/`method_col` name its community + delivery-mode columns.
    Stage 01 fills a blank facility mode by community-name match, then by nearest marker within
    `max_dist_m`. Region-agnostic: all values are profile DATA.
    """

    path: str
    community_col: str
    method_col: str
    max_dist_m: float = 5000.0


class PipelineConfig(_Strict):
    """The resolved layer/transfer registry plus paths. Built from a RegionProfile (or layers.yaml).

    `_project_dir` overrides the base used to resolve relative roots — the profile sets it to the
    profile's own directory so a profile can ship with relative paths next to it.
    """

    roots: dict[str, str]
    crs: CRS = Field(default_factory=CRS)
    layers: list[LayerSpec]
    transfers: list[TransferSpec] = Field(default_factory=list)
    bridges: list[BridgeSpec] = Field(default_factory=list)
    connect_to_giant: ConnectToGiantSpec = Field(default_factory=ConnectToGiantSpec)
    join_components: JoinComponentsSpec = Field(default_factory=JoinComponentsSpec)
    snaps: list[SnapSpec] = Field(default_factory=list)
    anchors: dict[str, str] = Field(default_factory=dict)
    place_tagging: Optional[PlaceTagging] = None
    boundary: Optional[str] = None
    border_stitch_m: float = 5000.0
    raw: dict[str, str]
    facility_columns: dict[str, str] = Field(default_factory=dict)
    capacity_columns: list[str] = Field(default_factory=list)
    routable_modes: list[str] = Field(default_factory=list)
    tagging_enabled: bool = True
    places_cols: dict[str, str] = Field(default_factory=dict)
    regions_cols: dict[str, str] = Field(default_factory=dict)
    delivery_fallback: Optional[DeliveryFallback] = None
    _project_dir: Path = PrivateAttr(default=PROJECT_DIR)

    def with_project_dir(self, base: Path) -> "PipelineConfig":
        self._project_dir = base
        return self

    # --- path resolution -------------------------------------------------
    def _resolve(self, ref: str) -> Path:
        """Resolve a `root/sub/path` reference (or absolute path) to an absolute Path."""
        base_dir = self._project_dir
        p = Path(ref)
        if p.is_absolute():
            return p
        head, _, tail = ref.partition("/")
        if head in self.roots:
            base = Path(self.roots[head])
            if not base.is_absolute():
                base = (base_dir / base).resolve()
            return (base / tail).resolve() if tail else base
        return (base_dir / ref).resolve()

    def layer_by_name(self, name: str) -> LayerSpec:
        for spec in self.layers:
            if spec.name == name:
                return spec
        raise KeyError(f"no layer named {name!r}; known: {[s.name for s in self.layers]}")

    def layer_paths(self, spec: LayerSpec) -> list[Path]:
        return [self._resolve(p) for p in (*spec.paths, *spec.extra_paths)]

    def anchor_path(self, anchor: str) -> Path:
        return self._resolve(self.anchors[anchor])

    def raw_path(self, key: str) -> Path:
        return self._resolve(self.raw[key])

    def place_path(self) -> Path:
        assert self.place_tagging is not None
        return self._resolve(self.place_tagging.places)

    def region_path(self) -> Path:
        assert self.place_tagging is not None
        return self._resolve(self.place_tagging.regions)

    def boundary_path(self) -> Path | None:
        return self._resolve(self.boundary) if self.boundary else None

    def delivery_fallback_path(self) -> Path | None:
        return self._resolve(self.delivery_fallback.path) if self.delivery_fallback else None


class Params(_Strict):
    """Model parameters, distances in meters. Only the knobs the gold pipeline consumes."""

    seed: int = 1234
    dedup_tol_m: float = 10.0
    buffer_dist: float = 5000.0
    hub_threshold_method: Literal["percentile", "jenks", "absolute"] = "percentile"
    hub_percentile: float = 0.90
    hub_abs_threshold: float = 500000.0
    precision: float = 1.0
    title: str = "mmnet — multimodal network"
    group_by: list[str] = Field(default_factory=lambda: ["community", "delivery_method"])
    tagging_enabled: bool = True


# --------------------------------------------------------------------------- RegionProfile
class FileSource(_Strict):
    """A pointer to one input file (room for `type: db|wfs|...` later; only `file` today)."""

    type: Literal["file"] = "file"
    path: str


class InventorySpec(_Strict):
    """Where the raw point inventory lives and which CSV columns map to internal names.

    Logical fields: id, lon, lat, capacity, delivery_method, community. `extra_capacity` lists
    additional capacity columns to merge with max() (per-fuel breakdowns). `name`/`type`/`entity`
    are optional descriptive columns. Every value is a raw CSV header name.
    """

    path: str
    id: str
    lon: str
    lat: str
    capacity: str
    delivery_method: str
    community: str
    name: Optional[str] = None
    entity: Optional[str] = None
    type: Optional[str] = None
    extra_capacity: list[str] = Field(default_factory=list)
    delivery_method_fallback: Optional[DeliveryFallback] = None   # fill blank modes from a community layer


class ModeSpec(_Strict):
    name: str
    routable: bool = True


class _ColMap(_Strict):
    path: str
    name_col: str
    id_col: Optional[str] = None
    region_col: Optional[str] = None


class TaggingSpec(_Strict):
    """Optional community/region tagging. When disabled, s01b_tag becomes a pass-through."""

    enabled: bool = True
    places: Optional[_ColMap] = None
    regions: Optional[_ColMap] = None


class ProfileLayerSource(_Strict):
    name: str
    mode: str
    edge_label: str
    kind: Literal["line", "point"] = "line"
    loader: Optional[str] = None
    source: Optional[FileSource] = None
    extra_source: Optional[FileSource] = None
    snap_target: bool = False   # hubs snap onto this layer's nodes (the ground surface)


class HubParams(_Strict):
    threshold_method: Literal["percentile", "jenks", "absolute"] = "percentile"
    percentile: float = 0.90
    abs_threshold: float = 500000.0
    buffer_dist: float = 5000.0
    dedup_tol_m: float = 10.0
    group_by: list[str] = Field(default_factory=lambda: ["community", "delivery_method"])


class TopologyParams(_Strict):
    precision: float = 1.0


class RegionProfile(_Strict):
    """The single source of truth for one region. Everything the engine treats as DATA lives here."""

    schema_version: int = 1
    title: str = "mmnet — multimodal network"
    crs: CRS = Field(default_factory=CRS)
    threshold_units: Literal["meters", "feet", "degrees"] = "meters"
    roots: dict[str, str] = Field(default_factory=dict)
    inventory: InventorySpec
    boundary: Optional[FileSource] = None
    modes: list[Union[ModeSpec, str]] = Field(default_factory=list)
    tagging: TaggingSpec = Field(default_factory=TaggingSpec)
    layers: list[ProfileLayerSource] = Field(default_factory=list)
    transfers: list[TransferSpec] = Field(default_factory=list)
    bridges: list[BridgeSpec] = Field(default_factory=list)
    connect_to_giant: ConnectToGiantSpec = Field(default_factory=ConnectToGiantSpec)
    join_components: JoinComponentsSpec = Field(default_factory=JoinComponentsSpec)
    snaps: list[SnapSpec] = Field(default_factory=list)
    anchors: dict[str, FileSource] = Field(default_factory=dict)
    hubs: HubParams = Field(default_factory=HubParams)
    topology: TopologyParams = Field(default_factory=TopologyParams)
    seed: int = 1234

    # set after load so relative roots resolve against the profile's own directory.
    _profile_dir: Path = PrivateAttr(default=PROJECT_DIR)

    def mode_names(self) -> list[str]:
        return [m if isinstance(m, str) else m.name for m in self.modes]

    def routable_modes(self) -> list[str]:
        out = []
        for m in self.modes:
            if isinstance(m, str):
                out.append(m)
            elif m.routable:
                out.append(m.name)
        return out

    # --- projections onto the legacy models the native steps consume -----
    def to_pipeline_config(self) -> PipelineConfig:
        layers: list[LayerSpec] = []
        for ls in self.layers:
            paths = [ls.source.path] if ls.source else []
            extra = [ls.extra_source.path] if ls.extra_source else []
            layers.append(LayerSpec(
                name=ls.name, mode=ls.mode, edge_label=ls.edge_label, kind=ls.kind,
                loader=ls.loader or "load_lines", paths=paths, extra_paths=extra,
                snap_target=ls.snap_target,
            ))

        # internal facility column map (raw header -> internal snake_case) the readers expect.
        inv = self.inventory
        facility_columns: dict[str, str] = {
            inv.id: "ast_facility_id",
            inv.community: "community_name",
            inv.delivery_method: "delivery_method",
            inv.capacity: "total_capacity",
            inv.lon: "longitude",
            inv.lat: "latitude",
        }
        if inv.entity:
            facility_columns[inv.entity] = "entity_name"
        capacity_columns = ["total_capacity"]
        for extra in inv.extra_capacity:
            internal = _snake(extra)
            facility_columns[extra] = internal
            capacity_columns.insert(-1, internal)  # keep total_capacity last (R order)

        place_tagging = None
        places_cols: dict[str, str] = {}
        regions_cols: dict[str, str] = {}
        if self.tagging.enabled and self.tagging.places and self.tagging.regions:
            place_tagging = PlaceTagging(
                places=self.tagging.places.path, regions=self.tagging.regions.path
            )
            p = self.tagging.places
            r = self.tagging.regions
            places_cols = {"name": p.name_col, **({"id": p.id_col} if p.id_col else {})}
            regions_cols = {"name": r.name_col, **({"region": r.region_col} if r.region_col else {})}

        raw: dict[str, str] = {"facilities": inv.path}

        cfg = PipelineConfig(
            roots=dict(self.roots),
            crs=self.crs,
            layers=layers,
            transfers=list(self.transfers),
            bridges=list(self.bridges),
            connect_to_giant=self.connect_to_giant,
            join_components=self.join_components,
            snaps=list(self.snaps),
            anchors={k: v.path for k, v in self.anchors.items()},
            place_tagging=place_tagging,
            boundary=self.boundary.path if self.boundary else None,
            raw=raw,
            facility_columns=facility_columns,
            capacity_columns=capacity_columns,
            routable_modes=self.routable_modes(),
            tagging_enabled=self.tagging.enabled,
            places_cols=places_cols,
            regions_cols=regions_cols,
            delivery_fallback=inv.delivery_method_fallback,
        )
        return cfg.with_project_dir(self._profile_dir)

    def to_params(self) -> Params:
        h, t = self.hubs, self.topology
        return Params(
            seed=self.seed,
            dedup_tol_m=h.dedup_tol_m,
            buffer_dist=h.buffer_dist,
            hub_threshold_method=h.threshold_method,
            hub_percentile=h.percentile,
            hub_abs_threshold=h.abs_threshold,
            precision=t.precision,
            title=self.title,
            group_by=list(h.group_by),
            tagging_enabled=self.tagging.enabled,
        )


def _snake(name: str) -> str:
    """Best-effort CamelCase/space -> snake_case for derived internal column names."""
    import re

    s = re.sub(r"[\s\-]+", "_", name.strip())
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s)
    return s.lower()


# --------------------------------------------------------------------------- loaders
def load_profile(path: str | Path) -> RegionProfile:
    """Parse + validate a RegionProfile YAML; record its directory for relative-path resolution."""
    path = Path(path)
    data = yaml.safe_load(path.read_text())
    prof = RegionProfile.model_validate(data)
    prof._profile_dir = path.resolve().parent
    return prof


def load_config(layers_path: str | Path | None = None) -> PipelineConfig:
    """Back-compat: a resolved PipelineConfig, from the active profile when available.

    Explicit `layers_path` still loads the legacy layers.yaml directly.
    """
    if layers_path is not None:
        data = yaml.safe_load(Path(layers_path).read_text())
        return _legacy_pipeline_config(data)
    prof_path = active_profile_path()
    if prof_path is not None:
        return load_profile(prof_path).to_pipeline_config()
    raise RuntimeError(
        "no profile configured: set MMNET_PROFILE (or legacy NETWEAVE_PROFILE) "
        "or call mmnet.run_pipeline(profile_path)"
    )


def _legacy_pipeline_config(data: dict) -> PipelineConfig:
    """Load the old layers.yaml shape (facilities-sourced) into a PipelineConfig.

    The inventory column map, capacity columns, routable modes, and polygon column names are DATA
    and live in the YAML (no region-specific constants in code). Absent keys default to empty, in
    which case the readers raise rather than silently assume a particular region's schema.
    """
    return PipelineConfig.model_validate(data)


def load_params(params_path: str | Path | None = None) -> Params:
    """Back-compat: Params from the active profile when available, else legacy params.yaml."""
    if params_path is not None:
        data = yaml.safe_load(Path(params_path).read_text())
        return Params.model_validate(data)
    prof_path = active_profile_path()
    if prof_path is not None:
        return load_profile(prof_path).to_params()
    raise RuntimeError(
        "no profile configured: set MMNET_PROFILE (or legacy NETWEAVE_PROFILE) "
        "or call mmnet.run_pipeline(profile_path)"
    )


# --------------------------------------------------------------------------- validation
_GEOGRAPHIC_CRS = {4326, 4269, 4267, 4258}  # common geographic (degree) CRSs


def validate_config(
    layers_path: str | Path | None = None, params_path: str | Path | None = None
) -> tuple[PipelineConfig, Params, list[str]]:
    """Load + validate config and report any referenced files that are missing.

    Returns (config, params, warnings). Raises pydantic ValidationError on a bad schema.
    """
    cfg = load_config(layers_path)
    params = load_params(params_path)
    warnings: list[str] = []

    cfg.model_dump()
    params.model_dump()

    checks: list[tuple[str, Path]] = [("raw.facilities", cfg.raw_path("facilities"))]
    if cfg.place_tagging is not None:
        checks.append(("place_tagging.places", cfg.place_path()))
        checks.append(("place_tagging.regions", cfg.region_path()))
    for anchor in cfg.anchors:
        checks.append((f"anchors.{anchor}", cfg.anchor_path(anchor)))
    for spec in cfg.layers:
        for p in cfg.layer_paths(spec):
            checks.append((f"layer:{spec.name}", p))

    for label, p in checks:
        if not p.exists():
            warnings.append(f"missing [{label}]: {p}")

    return cfg, params, warnings


def validate_profile(profile_path: str | Path) -> tuple[RegionProfile, list[str]]:
    """Deep validation of a RegionProfile: schema round-trip, CRS/unit guard, file + column checks.

    Returns (profile, problems). An empty problems list means PASS. Raises pydantic ValidationError
    on a schema/unknown-key violation (caught + reported by the CLI).
    """
    prof = load_profile(profile_path)
    prof.model_dump()  # round-trip
    cfg = prof.to_pipeline_config()
    problems: list[str] = []

    # CRS / unit guard: a geographic (degree) target CRS cannot carry meter thresholds.
    if prof.threshold_units == "meters" and prof.crs.target in _GEOGRAPHIC_CRS:
        problems.append(
            f"crs.target={prof.crs.target} is geographic (degrees) but threshold_units=meters; "
            "use a projected (meters) target CRS, or set threshold_units to degrees."
        )

    # Every referenced file must exist.
    checks: list[tuple[str, Path]] = [("inventory.path", cfg.raw_path("facilities"))]
    if cfg.place_tagging is not None:
        checks.append(("tagging.places", cfg.place_path()))
        checks.append(("tagging.regions", cfg.region_path()))
    if cfg.delivery_fallback is not None:
        checks.append(("inventory.delivery_method_fallback", cfg.delivery_fallback_path()))
    for anchor in cfg.anchors:
        checks.append((f"anchors.{anchor}", cfg.anchor_path(anchor)))
    for spec in cfg.layers:
        for p in cfg.layer_paths(spec):
            checks.append((f"layer:{spec.name}", p))
    for label, p in checks:
        if not p.exists():
            problems.append(f"missing file [{label}]: {p}")

    # Every named inventory column must exist in the CSV header.
    inv = prof.inventory
    inv_path = cfg.raw_path("facilities")
    if inv_path.exists():
        header = _csv_header(inv_path)
        if header is not None:
            named = {
                "inventory.id": inv.id, "inventory.lon": inv.lon, "inventory.lat": inv.lat,
                "inventory.capacity": inv.capacity, "inventory.delivery_method": inv.delivery_method,
                "inventory.community": inv.community,
            }
            for opt_label, val in (("inventory.name", inv.name), ("inventory.entity", inv.entity),
                                   ("inventory.type", inv.type)):
                if val:
                    named[opt_label] = val
            for i, col in enumerate(inv.extra_capacity):
                named[f"inventory.extra_capacity[{i}]"] = col
            for label, col in named.items():
                if col not in header:
                    problems.append(f"inventory column [{label}]={col!r} not in CSV header of {inv_path.name}")

    return prof, problems


def _csv_header(path: Path) -> list[str] | None:
    try:
        import csv

        with path.open(encoding="utf-8-sig", newline="") as fh:
            return next(csv.reader(fh))
    except Exception:
        return None
