#!/usr/bin/env bash
set -euo pipefail

python -m flake8 . --exclude=.venv
python -m isort --check-only . --skip .venv
python -m black --check . --exclude ".venv/"

pytest -q
