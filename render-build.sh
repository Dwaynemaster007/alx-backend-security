#!/usr/bin/env bash
set -o errexit

# UPGRADE PIP SYSTEM-WIDE
python -m pip install --upgrade pip setuptools wheel

# SYSTEM-WIDE INSTALL — BYPASS ALL VENVS
python -m pip install -r requirements.txt --no-cache-dir --force-reinstall

# FORCE INSTALL MISSING DJANGO DEPS (asgiref, sqlparse, etc.)
python -m pip install asgiref sqlparse tzdata --force-reinstall

# DJANGO COMMANDS
python manage.py collectstatic --no-input --clear
python manage.py migrate --no-input
