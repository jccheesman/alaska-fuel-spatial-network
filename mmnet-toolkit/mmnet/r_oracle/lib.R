# lib.R — self-contained R noder for the mmnet build oracle.
# =============================================================================
# The gold pipeline uses R for ONE job: build the per-mode sfnetwork — the planar
# noding + subdivision + smoothing that is hard to reproduce exactly in Python.
# `clean_subnetwork()` (copied VERBATIM from the Alaska R preprocess project
# network_preprocess/R/network_preprocessing.R) is the whole surface that
# build_network.R --node-only needs. Python owns everything else: hub aggregation
# (Stage 02) and the intermodal connection (mmnet.assemble.connect_multimodal).
# lib.R sources NO Alaska project and reads NO {targets} cache.
# =============================================================================

suppressMessages({
  library(sf)
  library(dplyr)
  library(sfnetworks)
  library(tidygraph)
  library(igraph)
})

`%||%` <- function(a, b) if (is.null(a)) b else a

#' Clean a subnetwork: round coords, node at crossings, subdivide, smooth. (VERBATIM)
#' target_crs is required; call sites must supply it.
clean_subnetwork <- function(sf_data, label, precision = 1, target_crs) {
  sf::st_agr(sf_data) <- "constant"
  sf::st_geometry(sf_data) <- sf::st_geometry(sf_data) |>
    sf::st_as_binary(precision = precision) |>
    sf::st_as_sfc() |>
    sf::st_set_crs(sf::st_crs(sf_data))

  # Planar-node the lines at every intersection FIRST, so segments that cross WITHOUT a
  # shared vertex become connected. to_spatial_subdivision only splits at already-shared
  # interior points; it does not insert new vertices at geometric crossings — st_node() does.
  # (Without this, a road grid whose lines cross without shared endpoints fragments and
  #  edges are dropped.)
  noded <- sf::st_geometry(sf_data) |>
    sf::st_union() |>
    sf::st_node() |>
    sf::st_cast("LINESTRING")
  sf_data <- sf::st_sf(geometry = noded)
  sf::st_agr(sf_data) <- "constant"

  sfnetworks::as_sfnetwork(sf_data, directed = FALSE) |>
    tidygraph::convert(sfnetworks::to_spatial_subdivision) |>
    tidygraph::convert(sfnetworks::to_spatial_smooth) |>
    tidygraph::activate("edges") |>
    dplyr::mutate(type = label) |>
    # Drop tidygraph's internal bookkeeping indices: to_spatial_subdivision makes
    # `.tidygraph_edge_index` a LIST when edges split but INTEGER when they don't, which
    # breaks the cross-mode st_network_join (bind_rows can't combine list vs integer).
    dplyr::select(-dplyr::any_of(".tidygraph_edge_index")) |>
    tidygraph::activate("nodes") |>
    dplyr::select(-dplyr::any_of(".tidygraph_node_index"))
}
