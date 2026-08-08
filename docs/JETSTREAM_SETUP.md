# Jetstream2 VM Setup Guide — (friction + network)

Optional guide for running the friction-surface build, network ingest, and
edge weighting on a Jetstream2 VM. The pipeline is CPU-only (numpy / rasterio /
duckdb) — **no GPU or LLM backend is required**. A local workstation with
enough RAM for the statewide 150 m rasters works equally well.

---

## A. Setting Up a New Instance

### 1. Create the VM (Jetstream2 Web UI)

- **Image**: Ubuntu (latest LTS)
- **Size**: a CPU flavor with generous RAM (the statewide 150 m rasters are
  large); no GPU needed
- **Root Disk**: 150 GB

### 2. Attach Storage Volume

- Attach an existing volume (or create one, 200 GB+ recommended)
- The volume persists your code, venv, and data between instances

### 3. Open a Terminal (Guacamole Desktop) and load the env manager

```bash
module load miniforge
cd /media/volume/<your-volume-name>
```

### 4. Set Up the Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 5. Get the project onto the VM

```bash
git clone <this-repo> && cd <this-repo> && git lfs pull
uv venv && uv sync && uv pip install -e .
python tools/extract_inputs.py
```

### 6. Install Dependencies

```bash
pip install -r requirements.txt
# supplementary install commands, if any:
#   see installations.txt
```

### 7. Run the Pipeline

Use `tmux` so long runs survive a Guacamole disconnect:

```bash
tmux new -s pipeline

# 1. Build the friction surfaces
python -m friction_surface.run_friction_pipeline

# 2. Ingest the delivered network
python load_final_network.py

# 3. Weight each edge
python weight_network_edges.py
python assemble_weighted_graph.py

# Detach: Ctrl+B then D.  Reattach: tmux attach -t pipeline
```

---

## B. Reopening an Existing Instance

```bash
module load miniforge
cd /media/volume/<your-volume-name>
source venv/bin/activate
tmux new -s pipeline
```

---

## C. Quick Reference

| Item | Value |
|---|---|
| GPU | not required (CPU-only pipeline) |
| Root Disk | 150 GB |
| Volume | 200 GB+ (attached, persists between instances) |
| Python venv | `/media/volume/<name>/venv` |
| Friction build | `python -m friction_surface.run_friction_pipeline` |
| Network ingest | `python load_final_network.py` |
| Edge weighting | `python weight_network_edges.py` → `python assemble_weighted_graph.py` |

---

## D. Troubleshooting

- **Out of memory during the friction build**: `build_mode_friction` accepts a
  `window` argument for tile-based processing (off by default).
- **Volume not mounted after reboot**: `sudo mount -a`.
- **Permission denied on a script**: `chmod +x <script-name>`.
