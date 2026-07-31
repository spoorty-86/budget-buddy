#!/usr/bin/env bash
# BudgetBuddy backend — one command to set up and run.
# Usage: ./run.sh
set -e

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "==> Creating virtual environment..."
  python3 -m venv venv
fi

echo "==> Activating virtual environment..."
source venv/bin/activate

echo "==> Installing dependencies..."
pip install -q -r requirements.txt

echo "==> Applying database migrations..."
python manage.py migrate

echo ""
echo "==> Starting server at http://127.0.0.1:8000/"
echo ""
python manage.py runserver 127.0.0.1:8000
