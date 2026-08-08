#!/usr/bin/env bash
# Shared helpers for the four workflow run_all.sh drivers.
#
# Solves three problems the per-stage scripts used to have independently:
#   1. they called bare `python3`, silently running against system Python
#      instead of the project venv (and failing on imports);
#   2. stage 02 piped every step through `| grep ... || true`, which discards
#      the real exit status — the script reported success on a failed build;
#   3. a missing input and a genuine crash both exited 1, so the top-level
#      run_all.sh could not tell "skip, data absent" from "this is broken".
#
# Source it with:  . "$(dirname "$0")/../_lib.sh"
# It expects ROOT to be set (the repo root) before sourcing.

# Exit code reserved for "required input absent — skip this stage, not a bug".
# The top-level run_all.sh treats it as a skip; anything else is a failure.
GATE_EXIT=3

# ---------------------------------------------------------------------------
# Interpreter resolution: prefer an active venv, then the project's .venv,
# then fall back to python3 with a warning. Never silently use system Python.
# ---------------------------------------------------------------------------
resolve_python() {
  if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    PY="$VIRTUAL_ENV/bin/python"
  elif [ -x "$ROOT/.venv/bin/python" ]; then
    PY="$ROOT/.venv/bin/python"
  else
    PY="${PYTHON:-python3}"
    echo "WARNING: no project venv found; falling back to '$PY'." >&2
    echo "         Create one with: uv venv && uv sync && uv pip install -e ." >&2
  fi
  export PY
}

# ---------------------------------------------------------------------------
# gate MESSAGE...  — required input missing. Prints the message and exits with
# GATE_EXIT so the caller can distinguish a skip from a crash.
# ---------------------------------------------------------------------------
gate() {
  echo "GATE: $1"
  shift
  for line in "$@"; do echo "  $line"; done
  exit "$GATE_EXIT"
}

# ---------------------------------------------------------------------------
# run_step LABEL CMD...  — run a pipeline step, filtering known-noisy lines
# from the output while PRESERVING the command's real exit status. Aborts the
# stage on failure (the old `| grep | || true` form could not).
#
# Set FILT to an extended-regex of lines to suppress; unset means no filtering.
# ---------------------------------------------------------------------------
run_step() {
  local label="$1"; shift
  local log rc
  log="$(mktemp)"
  set +e
  "$@" >"$log" 2>&1
  rc=$?
  set -e
  if [ -n "${FILT:-}" ]; then
    grep -vE "$FILT" "$log" || true
  else
    cat "$log"
  fi
  rm -f "$log"
  if [ "$rc" -ne 0 ]; then
    echo >&2
    echo "ERROR: $label failed (exit $rc): $*" >&2
    exit "$rc"
  fi
}
