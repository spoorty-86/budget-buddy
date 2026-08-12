# BudgetBuddy Production Deployment Guide

This guide provides end-to-end instructions for deploying the **BudgetBuddy Django Backend** to **Render** or **AWS**, and the **React (Vite) Frontend** to **Vercel** (or Netlify).

---

## 🏗️ 1. Architecture Overview

```
 ┌───────────────────────────┐         REST API (HTTPS)          ┌───────────────────────────┐
 │   Vercel (Frontend)       │ ─────────────────────────────────>│     Render / AWS (Backend)│
 │   React 19 + Vite         │                                   │     Django 6 + Gunicorn   │
 └───────────────────────────┘                                   └─────────────┬─────────────┘
                                                                               │
                                                                               │ SQL Connection
                                                                               ▼
                                                                 ┌───────────────────────────┐
                                                                 │  Managed PostgreSQL DB    │
                                                                 └───────────────────────────┘
```

---

## 🔐 2. Environment Variables & Secrets Reference

> [!IMPORTANT]
> **Never commit actual passwords, secret keys, or API tokens to source control.**
> All secret environment variables must be configured directly within the target cloud platform's deployment console.

### Backend Environment Variables (Render / AWS)

| Environment Variable | Description | Recommended Production Setting |
| :--- | :--- | :--- |
| `DEBUG` | Disables debug mode in production | `False` |
| `SECRET_KEY` | Django standard security key | `django-insecure-generate-a-strong-random-key` |
| `JWT_SECRET_KEY` | Dedicated signing key for SimpleJWT tokens | `generate-a-unique-jwt-secret-key` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed host domains | `your-api.onrender.com` |
| `DATABASE_URL` | PostgreSQL connection URI containing credentials | `postgres://user:password@ep-xyz.postgres.render.com/budgetbuddy` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins | `https://your-app.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of CSRF-trusted origins | `https://your-app.vercel.app` |
| `EMAIL_HOST_USER` | SMTP username for outbound notification emails | `notifications@yourdomain.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password / API token for email service | `your-smtp-api-password` |

### Frontend Environment Variables (Vercel)

| Environment Variable | Description | Recommended Production Setting |
| :--- | :--- | :--- |
| `VITE_API_URL` | Base URL of the deployed Django REST API | `https://your-api.onrender.com` |

---

## 🐍 3. Backend Deployment

### Option A: Deploying Backend to Render (Recommended)

1. **Connect Repository**:
   - Log into [Render Console](https://dashboard.render.com/) and click **New +** -> **Blueprint**.
   - Connect your GitHub repository. Render automatically reads `backend/render.yaml`.

2. **Manual Web Service Creation (Alternative)**:
   - Click **New +** -> **Web Service**.
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command**:
     ```bash
     gunicorn budgetbuddy.wsgi:application --bind 0.0.0.0:$PORT
     ```

3. **Database Provisioning (Render PostgreSQL)**:
   - Click **New +** -> **PostgreSQL**.
   - Copy the **Internal Database URL** or **External Database URL**.
   - Set the `DATABASE_URL` key under your Web Service **Environment Settings**.

4. **Set Environment Variables on Render**:
   - In the Render Web Service dashboard (`your-api.onrender.com`), go to **Environment** and configure:
     - `DEBUG` = `False`
     - `SECRET_KEY` = `<strong-random-string>`
     - `JWT_SECRET_KEY` = `<strong-random-string>`
     - `ALLOWED_HOSTS` = `your-api.onrender.com`
     - `DATABASE_URL` = `<your-render-postgres-url>`
     - `CORS_ALLOWED_ORIGINS` = `https://your-app.vercel.app`
     - `CSRF_TRUSTED_ORIGINS` = `https://your-app.vercel.app`

---

### Option B: Deploying Backend to AWS

#### Using AWS App Runner

1. Create an **AWS App Runner** service linked to your repository.
2. Set the **Build Settings**:
   - Runtime: `Python 3`
   - Build Command: `pip install -r backend/requirements.txt && python backend/manage.py collectstatic --noinput && python backend/manage.py migrate`
   - Start Command: `gunicorn backend.budgetbuddy.wsgi:application --bind 0.0.0.0:8080`
   - Port: `8080`
3. Provision an **AWS RDS PostgreSQL** instance.
4. Add environment variables in AWS App Runner Configuration:
   - `DATABASE_URL`: `postgres://dbuser:dbpassword@rds-instance-endpoint.amazonaws.com:5432/budgetbuddy`
   - `SECRET_KEY`, `JWT_SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.

---

## ⚡ 4. Frontend Deployment (Vercel)

1. **Connect Repository**:
   - Log into [Vercel Dashboard](https://vercel.com/) and click **Add New** -> **Project**.
   - Import your GitHub repository.

2. **Configure Project Settings**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

3. **Configure Environment Variables**:
   - In Vercel Project Settings under **Environment Variables**, add:
     - Key: `VITE_API_URL`
     - Value: `https://your-api.onrender.com`

4. **SPA Routing**:
   - `frontend/vercel.json` handles URL rewrites automatically so client-side routes (e.g. `/expenses`, `/budgets`, `/categories`) reload seamlessly without 404 errors.

---

## 🌐 5. CORS & SSL/HTTPS Configuration Guide

### 🔒 SSL / HTTPS Integration
Both **Vercel** (`your-app.vercel.app`) and **Render** (`your-api.onrender.com`) provide **free SSL certificates** and automatically handle HTTPS encryption.

When backend `DEBUG` is set to `False`, Django automatically activates:
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` (Informs Django that SSL is terminated at Render's reverse proxy).
- `SECURE_SSL_REDIRECT = True` (Redirects any HTTP requests to HTTPS).
- `SESSION_COOKIE_SECURE = True` & `CSRF_COOKIE_SECURE = True` (Restricts auth cookies to HTTPS connections).
- `SECURE_HSTS_SECONDS = 31536000` (Enforces HSTS security).

### 🚀 CORS & CSRF Step-by-Step Flow:
1. **Frontend Request**: The React app on `https://your-app.vercel.app` sends a REST API request to `https://your-api.onrender.com`.
2. **Browser Preflight**: The browser sends an `OPTIONS` request with `Origin: https://your-app.vercel.app`.
3. **Django CORS Headers**: `django-cors-headers` checks `CORS_ALLOWED_ORIGINS`. Because `CORS_ALLOWED_ORIGINS` contains `https://your-app.vercel.app`, Django returns:
   - `Access-Control-Allow-Origin: https://your-app.vercel.app`
   - `Access-Control-Allow-Credentials: true`
4. **Django CSRF Middleware**: `CSRF_TRUSTED_ORIGINS` includes `https://your-app.vercel.app`, ensuring unsafe HTTP methods (POST, PUT, DELETE) are permitted.

> [!TIP]
> If you experience CORS errors in the browser console:
> 1. Ensure `CORS_ALLOWED_ORIGINS` on the backend matches the **exact protocol and origin** of your frontend (including `https://` and without trailing slashes).
> 2. Ensure `ALLOWED_HOSTS` includes the backend domain.

---

## 🧪 6. Post-Deployment Verification Checklist

- [ ] **Backend Health**: Visit `https://<your-backend-domain>.onrender.com/api/auth/token/` to verify Django REST API responds.
- [ ] **Static Assets**: Verify `/admin/` CSS and JS load properly (served via WhiteNoise).
- [ ] **Frontend Routes**: Test navigating between Dashboard, Incomes, Expenses, Budgets, and Reports on Vercel.
- [ ] **Authentication Flow**: Register a new user account, log in, refresh token, and log out.
- [ ] **Database Persistence**: Create expenses and budgets; verify data persists across restarts.
