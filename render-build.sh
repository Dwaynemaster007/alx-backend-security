#!/usr/bin/bash
# render-build.sh — ALX Backend Security NOV 2025 FIXED

set -e

echo "Upgrading pip + setuptools + wheel"
pip install --upgrade pip setuptools wheel

echo "Installing requirements with NO CACHE + FORCE"
pip install -r requirements.txt --no-cache-dir --force-reinstall

echo "FORCE REINSTALL decorator (fixes hidden dependency)"
pip install decorator==5.1.1 --force-reinstall

echo "Collect static"
cd ip_tracking  # ← CRITICAL: CHANGE TO PROJECT DIR
python manage.py collectstatic --no-input --clear

echo "Running migrations"
python manage.py migrate --no-input

echo "Build successful! 🎉"