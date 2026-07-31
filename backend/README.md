# BudgetBuddy — Backend (Milestone 1 & 2)

This is the **backend only**. The frontend lives in a separate `frontend/` folder next to this one — see the root `README.md` for how to run both together.

## Milestone 1 — Requirements, Database Design & Backend Setup
- Django REST Framework backend initialized
- SQLite by default (swap to PostgreSQL by editing `DATABASES` in `budgetbuddy/settings.py`)
- JWT authentication (register / login / refresh)
- Full schema: Users, Profiles, Incomes, Expenses, Budgets, Savings Goals, Notifications, Reports

## Milestone 2 — Expense & Income Management
- Expense tracking CRUD API
- Income management CRUD API
- Expense categorization (Category model + FK)
- Budget creation system (per category/month, with live "spent" calculation)
- Transaction dashboard endpoint (totals, per-category breakdown, recent transactions)

## Setup & Run

**Fastest way — one script does everything (creates the venv, installs deps, migrates, runs):**

```bash
./run.sh
```

**Or manually, step by step:**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/

python manage.py runserver
```

### Real email delivery

The backend currently supports SMTP delivery via environment variables. Add a `.env` file in `backend/` or set these env vars before starting the server:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-smtp-username
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=BudgetBuddy <no-reply@example.com>
```

If you want to use Gmail SMTP, set:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Then restart the backend and registration emails will be sent to real inboxes.

Server runs at http://127.0.0.1:8000/

## API Endpoints

### Auth (Milestone 1)
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/auth/register/ | Create a user (username, email, password, full_name) |
| POST | /api/auth/login/ | Get JWT access + refresh tokens |
| POST | /api/auth/refresh/ | Refresh access token |
| GET/PATCH | /api/auth/me/ | Get/update own profile |

### Finance (Milestone 2)
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | /api/finance/categories/ | List/create categories |
| GET/POST | /api/finance/incomes/ | List/create incomes (own only) |
| GET/POST | /api/finance/expenses/ | List/create expenses (own only) |
| GET/POST | /api/finance/budgets/ | List/create budgets, includes computed `spent` |
| GET/POST | /api/finance/savings-goals/ | Savings goals CRUD |
| GET/POST | /api/finance/notifications/ | Notifications CRUD |
| GET/POST | /api/finance/reports/ | Reports CRUD |
| GET | /api/finance/dashboard/?month=7&year=2026 | Totals, category breakdown, recent transactions |

All `/api/finance/*` and `/api/auth/me/` endpoints require:
`Authorization: Bearer <access_token>`

## Example curl flow

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"testpass123","full_name":"Alice"}'

# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"testpass123"}'
# -> copy the "access" token from the response

TOKEN="paste-access-token-here"

# Create a category
curl -X POST http://127.0.0.1:8000/api/finance/categories/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Groceries","icon":"cart"}'

# Add an expense
curl -X POST http://127.0.0.1:8000/api/finance/expenses/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Weekly groceries","amount":"120.50","category":1,"date_spent":"2026-07-05"}'

# View dashboard
curl "http://127.0.0.1:8000/api/finance/dashboard/?month=7&year=2026" \
  -H "Authorization: Bearer $TOKEN"
```
