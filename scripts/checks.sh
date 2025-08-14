#!/usr/bin/env bash
set -euo pipefail

python3 -m flake8 . --exclude=.venv
python3 -m isort --check-only . --skip .venv
python3 -m black --check . --exclude ".venv/"

pytest -q
