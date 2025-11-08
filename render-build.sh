#!/usr/bin/env bash
set -o errexit

# SYSTEM-WIDE UPGRADE
python -m pip install --upgrade pip setuptools wheel --no-cache-dir

# FORCE SYSTEM INSTALL — BYPASS .venv COMPLETELY
python -m pip install -r requirements.txt --no-cache-dir --force-reinstall --no-deps

# EXPLICITLY INSTALL ALL HIDDEN DJANGO DEPS THAT BREAK IMPORTS
python -m pip install \
  asgiref>=3.7.0 \
  sqlparse>=0.5.0 \
  tzdata>=2024.1 \
  ratelimit>=4.1.0 \
  decorator>=5.1.1 \
  --force-reinstall --no-cache-dir

# DJANGO COMMANDS
python manage.py collectstatic --no-input --clear
python manage.py migrate --no-input
