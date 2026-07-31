#!/usr/bin/env bash
# BudgetBuddy frontend — one command to set up and run.
# Usage: ./run.sh
set -e

cd "$(dirname "$0")"

if [ ! -f ".env" ]; then
  echo "==> Creating .env from .env.example..."
  cp .env.example .env
fi

if [ ! -d "node_modules" ]; then
  echo "==> Installing dependencies (first run only)..."
  npm install
fi

echo ""
echo "==> Starting dev server at http://127.0.0.1:5173/"
echo "==> Make sure the backend is running at http://127.0.0.1:8000/"
echo ""
npm run dev
