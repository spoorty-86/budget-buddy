# BudgetBuddy

A personal budgeting app: track income and expenses, set category budgets, and watch savings goals grow.

Two separate codebases, meant to be run side by side in two terminals:

```
budgetbuddy/
├── backend/    Django REST API (Milestone 1 & 2)
└── frontend/   React + Vite app
```

## Run it (two terminals)

**Terminal 1 — backend:**

```bash
cd backend
./run.sh
```
Runs at http://127.0.0.1:8000/

**Terminal 2 — frontend:**

```bash
cd frontend
./run.sh
```
Runs at http://127.0.0.1:5173/

Open http://127.0.0.1:5173/ in your browser, register an account, and you're in.

Each `run.sh` sets itself up on first run (virtual env / `npm install`) and just starts the server on every run after that — no separate install step to remember, and no manual venv activation.

## What each side does

- **backend/** — Django REST Framework API: JWT auth, expenses, incomes, categories, budgets (with live "spent" totals), savings goals, and a dashboard endpoint. See `backend/README.md` for the full endpoint list and an example `curl` flow.
- **frontend/** — the UI that talks to that API. See `frontend/README.md` for the page list and how to point it at a different backend URL.

## Troubleshooting

- **Frontend loads but nothing works / network errors in the browser console** → the backend isn't running yet, or it's on a different port than `frontend/.env` expects (`VITE_API_URL`).
- **`./run.sh: Permission denied`** → run `chmod +x run.sh` once in that folder.
- **Port already in use** → something else is already running on 8000 or 5173; stop it, or edit the port in `backend/run.sh` / `frontend/vite.config.js`.
# infosys-springboard-internship
