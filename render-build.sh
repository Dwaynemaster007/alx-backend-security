#!/usr/bin/env bash
set -o errexit

# SYSTEM PIP — BYPASS ALL VENVS
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --no-cache-dir --force-reinstall --no-deps

# COLLECTSTATIC + MIGRATE
python manage.py collectstatic --no-input --clear
python manage.py migrate --no-input
