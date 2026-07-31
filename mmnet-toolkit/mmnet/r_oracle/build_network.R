#!/usr/bin/env Rscript
# build_network.R — the R node-only oracle for Stage 03 (mmnet `build`).
#
# R's ONE job in the gold pipeline: build the per-mode sfnetwork (the planar noding +
# subdivision + smoothing that is hard to reproduce exactly in Python). It does NOT
# aggregate hubs, blend, build transfers, or join the modes — Python owns hub
# aggregation (Stage 02) and the connection (mmnet.assemble.connect_multimodal).
#
# DECOUPLED: this oracle builds from a self-contained FILE CONTRACT in a temp WORKDIR
# assembled by the Python side (mmnet/build.py::_write_node_contract). It sources ONLY
# lib.R (same dir) — NO setwd to an Alaska R project, NO tar_read() from a {targets}
# cache. The Python wrapper loads the resulting edge GeoPackage into a NetworkTables.
#
# Usage: Rscript build_network.R --workdir <dir> --out <prefix> --modes Road,Plane --node-only
# Reads the node-only contract in <workdir> (see CONTRACT.md):
#   params.json (target_crs, precision), registry.json (modes), layers/<layer>.gpkg
# Writes <prefix>__edges.gpkg (geometry + type=edge_label); Python derives the global
# node table from the edge endpoints, so no nodes file is written.

suppressMessages({
  library(sf); library(sfnetworks); library(tidygraph); library(dplyr); library(jsonlite)
})

CONTRACT_VERSION <- "2"

args <- commandArgs(trailingOnly = TRUE)
getarg <- function(flag, default = NULL) {
  i <- which(args == flag)
  if (length(i) && i < length(args)) args[i + 1] else default
}
modes_sel  <- strsplit(getarg("--modes", "Road"), ",")[[1]]
workdir    <- getarg("--workdir")
out_prefix <- getarg("--out")
if (is.null(workdir))    stop("--workdir <dir> required")
if (is.null(out_prefix)) stop("--out <prefix> required")
if (!("--node-only" %in% args)) stop("build_network.R runs in --node-only mode only")
workdir    <- normalizePath(workdir, mustWork = TRUE)
out_prefix <- file.path(normalizePath(dirname(out_prefix), mustWork = FALSE), basename(out_prefix))

# Source ONLY the self-contained library (same dir as this script). No Alaska project, no cache.
this <- sub("^--file=", "", commandArgs(FALSE)[grepl("^--file=", commandArgs(FALSE))])
sys.source(file.path(dirname(this), "lib.R"), envir = globalenv())

# --- Read the file contract --------------------------------------------------
params_lst <- jsonlite::fromJSON(file.path(workdir, "params.json"))
if (!is.null(params_lst$contract_version) &&
    as.character(params_lst$contract_version) != CONTRACT_VERSION) {
  stop(sprintf("contract_version mismatch: file=%s, oracle=%s",
               params_lst$contract_version, CONTRACT_VERSION))
}
reg <- jsonlite::fromJSON(file.path(workdir, "registry.json"))
mr_all <- tibble::as_tibble(reg$modes)      # cols: mode, layer, edge_label, blend_param
mr <- mr_all[mr_all$mode %in% modes_sel, , drop = FALSE]
if (nrow(mr) == 0) stop("no modes from --modes match registry.json modes")

# --- Node each selected mode's lines -----------------------------------------
# Reuses clean_subnetwork() from lib.R verbatim and writes only <out>__edges.gpkg
# (geometry + type=edge_label).
target_crs <- as.integer(params_lst$target_crs)[1L]
if (is.null(target_crs) || is.na(target_crs)) stop("target_crs missing from contract params.json")
prec <- as.numeric(params_lst$precision %||% 1)[1L]
edges_list <- lapply(seq_len(nrow(mr)), function(k) {
  ly  <- sf::st_read(file.path(workdir, "layers", paste0(mr$layer[k], ".gpkg")), quiet = TRUE)
  cat(sprintf("  noding mode '%s' (%s): %d input lines\n",
              mr$mode[k], mr$edge_label[k], nrow(ly)), flush = TRUE)
  net <- clean_subnetwork(ly, mr$edge_label[k], prec, target_crs)
  e   <- sf::st_as_sf(net, "edges")
  e$type <- mr$edge_label[k]
  e[, "type"]
})
edges <- do.call(rbind, edges_list)
st_write(edges, paste0(out_prefix, "__edges.gpkg"), quiet = TRUE, delete_dsn = TRUE)
cat(sprintf("node-only: wrote %d noded edges across %d mode(s) -> %s__edges.gpkg\n",
            nrow(edges), nrow(mr), out_prefix), flush = TRUE)
