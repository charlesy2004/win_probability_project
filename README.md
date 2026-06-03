# NBA Win Probability Dashboard

An end-to-end NBA win probability dashboard that ingests live NBA game data, stores time-series game snapshots, applies a machine learning model, and serves predictions through a deployed full-stack web app.

The project combines live data ingestion, backend API development, database persistence, machine learning, and frontend visualization into one production-style data application.

---

## Live Project

- Frontend: Vercel
- Backend API: Render
- Database: Supabase Postgres
- Scheduled ingestion: GitHub Actions

---

## Architecture

```text
GitHub Actions Scheduler
        ↓
Render FastAPI Snapshot Endpoint
        ↓
ESPN Live NBA API
        ↓
XGBoost Win Probability Model
        ↓
Supabase Postgres
        ↓
Render FastAPI Read Endpoints
        ↓
Vercel React Dashboard