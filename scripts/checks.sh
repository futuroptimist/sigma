#!/usr/bin/env bash
set -euo pipefail

flake8 . --exclude=.venv
isort --check-only . --skip .venv
black --check . --exclude ".venv/"

pytest -q
