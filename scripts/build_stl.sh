#!/usr/bin/env bash
set -euo pipefail

SCAD_DIR="${SCAD_DIR:-hardware/scad}"
INPUT_DIR="${INPUT_DIR:-hardware/inputs}"
STL_DIR="${STL_DIR:-hardware/stl}"
CHECKSUM_MANIFEST="${CHECKSUM_MANIFEST:-hardware/stl/checksums.sha256}"

mkdir -p "$STL_DIR"

files=()
while IFS= read -r -d '' scad; do
  rel="${scad#$SCAD_DIR/}"
  stl="$STL_DIR/${rel%.scad}.stl"
  mkdir -p "$(dirname "$stl")"
  params=("$scad")
  input_json="$INPUT_DIR/${rel%.scad}.json"
  if [ -f "$input_json" ]; then
    mapfile -t defs < <(SIGMA_STL_PARAM_FILE="$input_json" python - <<'PY'
import json, os, sys

path = os.environ["SIGMA_STL_PARAM_FILE"]
with open(path, "r", encoding="utf-8") as fh:
    data = json.load(fh)
for key, value in data.items():
    if isinstance(value, (int, float)):
        print(f"-D{key}={value}")
    elif isinstance(value, str):
        print(f"-D{key}=\"{value}\"")
    else:
        raise SystemExit(f"Unsupported value type for {key}: {type(value).__name__}")
PY
    )
    params=("${defs[@]}" "$scad")
  fi

  if [ -f "$stl" ] && [ "$stl" -nt "$scad" ] && { [ ! -f "$input_json" ] || [ "$stl" -nt "$input_json" ]; }; then
    echo "[INFO] Skipping $scad; STL up to date"
  else
    echo "[INFO] Exporting $scad -> $stl"
    SIGMA_STL_PARAM_FILE="$input_json" openscad -o "$stl" "${params[@]}"
  fi
  files+=("$stl")
done < <(find "$SCAD_DIR" -name '*.scad' -print0 | sort -z)

if command -v sha256sum >/dev/null 2>&1; then
  printf "" > "$CHECKSUM_MANIFEST"
  for stl in "${files[@]}"; do
    sha256sum "$stl" >> "$CHECKSUM_MANIFEST"
  done
  echo "[INFO] Wrote checksum manifest to $CHECKSUM_MANIFEST"
else
  echo "[WARN] sha256sum not available; skipping checksum manifest" >&2
fi
