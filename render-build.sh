#!/usr/bin/env bash
set -o errexit

# FORCE SYSTEM PIP — BYPASS POETRY COMPLETELY
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --no-cache-dir --force-reinstall

python manage.py collectstatic --no-input --clear
python manage.py migrate --no-input
