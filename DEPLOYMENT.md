# BudgetBuddy Production Deployment Guide

This guide provides end-to-end instructions for deploying the **BudgetBuddy React (Vite) Frontend** to **Vercel** (URL: `https://budget-buddy-app.vercel.app`) and the **Django REST API Backend** to **Render** or **AWS**.

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

## ⚡ 2. Deploying Frontend to Vercel (Interactive Landing Page)

To deploy the frontend to Vercel:

1. **Import Repository on Vercel**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New** -> **Project**.
   - Select your GitHub repository (`spoorty-86/budget-buddy`).

2. **Configure Project Settings**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

3. **Set Environment Variable**:
   - Under **Environment Variables**, add:
     - `VITE_API_URL`: Your deployed backend REST API URL (e.g. `https://budgetbuddy-backend.onrender.com`).

4. **Deploy**:
   - Click **Deploy**. Vercel will build and assign a URL (e.g. `https://budget-buddy-nine-teal.vercel.app`).
   - When users open this link, they will see the **BudgetBuddy Landing Page** featuring:
     - Dark Mode / Light Mode toggle.
     - Project module showcase cards (Income, Expenses, Budgets, Savings Goals, Reports, Notifications, AI Assistant, Custom Categories).
     - Direct **Sign In** and **Get Started** options.

---

## 🐍 3. Deploying Backend to Render

1. **Connect Repository**:
   - Log into [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Blueprint**.
   - Select your GitHub repository. Render reads `backend/render.yaml` automatically.

2. **Set Environment Variables**:
   - `DEBUG` = `False`
   - `SECRET_KEY` = `<strong-random-secret-key>`
   - `JWT_SECRET_KEY` = `<strong-random-jwt-secret>`
   - `ALLOWED_HOSTS` = `budgetbuddy-backend.onrender.com`
   - `CORS_ALLOWED_ORIGINS` = `https://your-vercel-app-name.vercel.app`
   - `DATABASE_URL` = `<Render PostgreSQL Connection String>`

---

## 🧪 4. Post-Deployment Verification

- Open your Vercel URL (`https://your-app-name.vercel.app`).
- Verify the **Landing Page** renders smoothly with Light and Dark theme toggles.
- Click **Sign In** or **Get Started** to test authentication and navigate into the Dashboard.
