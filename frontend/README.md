# BudgetBuddy — Frontend (React + Vite)

This is the **frontend only**. It talks to the Django backend in the `backend/` folder next to this one — see the root `README.md` for how to run both together.

## Stack
- React 19 + Vite
- React Router for pages
- Axios for API calls (JWT access/refresh handled automatically)

## Pages
- Login / Register
- Dashboard — totals, spend-by-category, recent transactions (filter by month/year)
- Expenses, Incomes — add and list, own-user only
- Budgets — monthly limit per category with a live "spent" progress bar
- Categories — manage expense categories
- Savings Goals — track progress toward a target amount

## Setup & Run

**Fastest way — one script does everything (installs deps, starts dev server):**

```bash
./run.sh
```

**Or manually:**

```bash
cp .env.example .env   # only needed if backend isn't on the default URL
npm install
npm run dev
```

App runs at http://127.0.0.1:5173/ and expects the backend at http://127.0.0.1:8000/ (configurable in `.env` via `VITE_API_URL`).

## Build for production

```bash
npm run build
```

Outputs static files to `dist/`.
