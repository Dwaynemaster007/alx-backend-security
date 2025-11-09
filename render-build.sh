#!/bin/bash
set -e

echo "Upgrading pip + setuptools + wheel"
python -m pip install --upgrade pip setuptools wheel

echo "Installing requirements with NO CACHE + FORCE"
pip install --no-cache-dir -r requirements.txt

echo "FORCE REINSTALL decorator (fixes hidden dependency)"
pip install --force-reinstall --no-cache-dir decorator==5.1.1

echo "Collect static"
python manage.py collectstatic --no-input

echo "Migrate"
python manage.py migrate

echo "ALX BACKEND SECURITY READY — IP TRACKING + GEO + RATELIMIT + CELERY"