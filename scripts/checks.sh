#!/usr/bin/env bash
set -e

flake8 . --exclude=.venv
isort --check-only . --skip .venv
black --check . --exclude ".venv/"

pytest -q
