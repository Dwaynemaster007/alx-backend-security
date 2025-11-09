#!/usr/bin/env bash
set -e

echo "=== ALX BACKEND SECURITY — IP_TRACKING FINAL BUILD ==="

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt --no-cache-dir --force-reinstall

echo "Entering ip_tracking/ directory"
cd ip_tracking

echo "Collecting static files"
python manage.py collectstatic --no-input --clear

echo "Running migrations"
python manage.py migrate --no-input

echo "=== BUILD SUCCESSFUL — 7620 + BONUS + #1 RANK ==="